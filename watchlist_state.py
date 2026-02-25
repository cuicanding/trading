"""
自选股状态管理 - 简化版
"""
import reflex as rx
import aiohttp
import asyncio
from typing import List, Optional
from auth import AuthState
from models import WatchlistItemRepository, WatchlistGroupRepository
from stock_api import stock_api
from datetime import datetime

TECH_COLORS = {
    "primary": "#00f0ff",
    "secondary": "#7000ff",
    "success": "#00ff88",
    "error": "#ff3366",
    "light": "#ffffff",
    "gray": "#2a2a35",
    "darker": "#050508",
}


class WatchlistState(AuthState):
    watchlist_items: List[dict] = []
    groups: List[dict] = []
    selected_group: str = ""
    is_loading: bool = False
    error_message: str = ""
    success_message: str = ""
    
    add_stock_code: str = ""
    add_stock_name: str = ""
    show_add_dialog: bool = False
    search_results: List[dict] = []
    last_refresh_time: str = ""
    
    selected_stocks: List[dict] = []
    search_debounce_task: Optional[asyncio.Task] = None
    
    def load_watchlist(self):
        if not self.current_user_id:
            return
        self.is_loading = True
        try:
            item_repo = WatchlistItemRepository()
            items = item_repo.get_items_by_user(str(self.current_user_id))
            self.watchlist_items = []
            for item in items:
                d = item.to_dict()
                self.watchlist_items.append(d)
            self.last_refresh_time = datetime.now().strftime("%H:%M:%S")
        except Exception as e:
            self.error_message = f"加载失败: {str(e)}"
        finally:
            self.is_loading = False
    
    @rx.background
    async def refresh_prices(self):
        """后台异步刷新价格"""
        if not self.watchlist_items:
            return
        
        async with self.get_state(WatchlistState) as state:
            state.is_loading = True
            yield state
        
        codes = [item.get('stock_code', '') for item in self.watchlist_items]
        
        async with aiohttp.ClientSession() as session:
            tasks = [stock_api.get_realtime_quote_async(code, session) for code in codes]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        async with self.get_state(WatchlistState) as state:
            updated_items = []
            for i, item in enumerate(state.watchlist_items):
                result = results[i]
                if isinstance(result, dict) and result:
                    item['price'] = result.get('price', 0.0)
                    item['pct_chg'] = result.get('pct_chg', 0.0)
                    item['change'] = result.get('change', 0.0)
                    item['currency'] = result.get('currency', '¥')
                    item['stock_name'] = result.get('name', item.get('stock_name', ''))
                else:
                    item['price'] = 0
                    item['pct_chg'] = 0
                    item['change'] = 0
                updated_items.append(item)
            
            state.watchlist_items = updated_items
            state.last_refresh_time = datetime.now().strftime("%H:%M:%S")
            state.success_message = "刷新成功"
            state.is_loading = False
            yield state
    
    def open_add_dialog(self):
        self.show_add_dialog = True
        self.add_stock_code = ""
        self.add_stock_name = ""
        self.search_results = []
        self.error_message = ""
    
    def close_add_dialog(self):
        self.show_add_dialog = False
        self.add_stock_code = ""
        self.add_stock_name = ""
        self.search_results = []
    
    def set_add_stock_code(self, value: str):
        self.add_stock_code = value
        self.add_stock_name = ""
        if len(value) >= 1:
            self.search_results = stock_api.search_stock(value)
        else:
            self.search_results = []
    
    def select_stock(self, code: str, name: str):
        self.add_stock_code = code
        self.add_stock_name = name
        self.search_results = []
    
    def add_to_watchlist(self):
        if not self.current_user_id:
            self.error_message = "请先登录"
            return
        if not self.add_stock_code:
            self.error_message = "请输入股票代码"
            return
        try:
            item_repo = WatchlistItemRepository()
            code = self.add_stock_code.split('.')[0]
            if item_repo.item_exists(str(self.current_user_id), code):
                self.error_message = "已在自选股中"
                return
            name = self.add_stock_name
            if not name:
                info = stock_api.get_stock_info(code)
                name = info.get('name', '') if info else ''
            item_repo.add_item(
                user_id=str(self.current_user_id),
                stock_code=code,
                stock_name=name
            )
            self.success_message = f"已添加 {name or code}"
            self.show_add_dialog = False
            self.load_watchlist()
        except Exception as e:
            self.error_message = f"添加失败: {str(e)}"
    
    def remove_from_watchlist(self, item_id: str):
        try:
            item_repo = WatchlistItemRepository()
            item_repo.remove_item(item_id)
            self.success_message = "已删除"
            self.load_watchlist()
        except Exception as e:
            self.error_message = f"删除失败: {str(e)}"
    
    @rx.background
    async def search_with_debounce(self, value: str):
        """防抖搜索 - 300ms 延迟"""
        if self.search_debounce_task:
            self.search_debounce_task.cancel()
        
        async def do_search():
            await asyncio.sleep(0.3)
            if len(value) >= 1:
                async with aiohttp.ClientSession() as session:
                    results = await stock_api.search_stock_async(value, session)
                    async with self.get_state(WatchlistState) as state:
                        state.add_stock_code = value
                        state.search_results = results
                        yield state
        
        self.search_debounce_task = asyncio.create_task(do_search())
    
    def toggle_stock_selection(self, code: str, name: str):
        """切换股票选择状态"""
        for stock in self.selected_stocks:
            if stock['code'] == code:
                self.selected_stocks = [s for s in self.selected_stocks if s['code'] != code]
                return
        self.selected_stocks = self.selected_stocks + [{'code': code, 'name': name}]
    
    def clear_selection(self):
        """清空选择"""
        self.selected_stocks = []
    
    def parse_multiple_codes(self, input_str: str) -> List[str]:
        """解析逗号分隔的股票代码"""
        codes = [c.strip() for c in input_str.replace('，', ',').split(',') if c.strip()]
        return codes
    
    @rx.background
    async def add_multiple_to_watchlist(self):
        """批量添加自选股"""
        if not self.current_user_id:
            async with self.get_state(WatchlistState) as state:
                state.error_message = "请先登录"
                yield state
            return
        
        if not self.selected_stocks:
            async with self.get_state(WatchlistState) as state:
                state.error_message = "请选择股票"
                yield state
            return
        
        try:
            item_repo = WatchlistItemRepository()
            added_count = 0
            
            for stock in self.selected_stocks:
                code = stock['code'].split('.')[0]
                if not item_repo.item_exists(str(self.current_user_id), code):
                    item_repo.add_item(
                        user_id=str(self.current_user_id),
                        stock_code=code,
                        stock_name=stock.get('name', '')
                    )
                    added_count += 1
            
            async with self.get_state(WatchlistState) as state:
                state.success_message = f"已添加 {added_count} 只股票"
                state.selected_stocks = []
                state.show_add_dialog = False
                yield state
            
            self.load_watchlist()
        except Exception as e:
            async with self.get_state(WatchlistState) as state:
                state.error_message = f"添加失败: {str(e)}"
                yield state
