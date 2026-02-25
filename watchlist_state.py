"""
自选股状态管理 - 分组版
"""
import reflex as rx
import aiohttp
import asyncio
from typing import List
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


def _get_market(code: str) -> str:
    code = str(code).upper().replace('.SH', '').replace('.SZ', '').replace('.HK', '')
    if code.isalpha():
        return "US"
    if len(code) == 5 and code.isdigit():
        return "HK"
    return "A"


class WatchlistState(AuthState):
    watchlist_items: List[dict] = []
    index_quotes: List[dict] = []
    a_stocks: List[dict] = []
    hk_stocks: List[dict] = []
    us_stocks: List[dict] = []
    
    is_loading: bool = False
    is_refreshing: bool = False
    error_message: str = ""
    success_message: str = ""
    last_refresh_time: str = ""
    
    add_stock_code: str = ""
    add_stock_name: str = ""
    show_add_dialog: bool = False
    search_results: List[dict] = []
    selected_stocks: List[dict] = []
    
    _auto_refresh_enabled: bool = True

    @rx.var
    def a_indices(self) -> List[dict]:
        return [q for q in self.index_quotes if q.get("currency") == "¥"]

    @rx.var
    def hk_indices(self) -> List[dict]:
        return [q for q in self.index_quotes if q.get("currency") == "HK$"]

    @rx.var
    def us_indices(self) -> List[dict]:
        return [q for q in self.index_quotes if q.get("currency") == "$"]

    async def on_mount(self):
        if not self.current_user_id:
            return
        self.is_loading = True
        yield
        
        try:
            item_repo = WatchlistItemRepository()
            items = item_repo.get_items_by_user(str(self.current_user_id))
            self.watchlist_items = []
            for item in items:
                d = item.to_dict()
                d["price"] = "--"
                d["pct_chg"] = "--%"
                d["currency"] = "¥"
                d["market"] = _get_market(d.get("stock_code", ""))
                d["is_up"] = True
                self.watchlist_items.append(d)
        except Exception as e:
            self.error_message = f"加载失败: {str(e)}"
        
        self.is_loading = False
        yield
        
        await self._do_refresh()
        yield

    async def auto_refresh(self):
        """自动刷新，由前端定时器触发"""
        if not self.is_refreshing:
            await self._do_refresh()
            yield

    async def _do_refresh(self):
        if self.is_refreshing:
            return
        self.is_refreshing = True
        
        try:
            async with aiohttp.ClientSession() as session:
                tasks = [stock_api.get_index_quotes_async(session)]
                if self.watchlist_items:
                    codes = [item.get("stock_code", "") for item in self.watchlist_items]
                    tasks.extend([stock_api.get_realtime_quote_async(code, session) for code in codes])
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                self.index_quotes = results[0] if isinstance(results[0], list) else []
                
                if self.watchlist_items:
                    stock_results = results[1:]
                    updated_items = []
                    for i, item in enumerate(self.watchlist_items):
                        new_item = dict(item)
                        result = stock_results[i]
                        if isinstance(result, dict) and result and result.get("price", 0) > 0:
                            pct = result.get('pct_chg', 0)
                            new_item["price"] = f"{result.get('price', 0):.2f}"
                            new_item["pct_chg"] = f"{pct:+.2f}%"
                            new_item["currency"] = result.get("currency", "¥")
                            new_item["stock_name"] = result.get("name", new_item.get("stock_name", ""))
                            new_item["is_up"] = pct >= 0
                        updated_items.append(new_item)
                    self.watchlist_items = updated_items
                
                self._split_by_market()
                self.last_refresh_time = datetime.now().strftime("%H:%M:%S")
        except Exception as e:
            print(f"刷新行情失败: {e}")
        
        self.is_refreshing = False

    def _split_by_market(self):
        self.a_stocks = [i for i in self.watchlist_items if i.get("market") == "A"]
        self.hk_stocks = [i for i in self.watchlist_items if i.get("market") == "HK"]
        self.us_stocks = [i for i in self.watchlist_items if i.get("market") == "US"]

    def open_add_dialog(self):
        self.show_add_dialog = True
        self.add_stock_code = ""
        self.add_stock_name = ""
        self.search_results = []
        self.selected_stocks = []
        self.error_message = ""

    def close_add_dialog(self):
        self.show_add_dialog = False
        self.add_stock_code = ""
        self.add_stock_name = ""
        self.search_results = []
        self.selected_stocks = []

    async def search_with_debounce(self, value: str):
        self.add_stock_code = value
        await asyncio.sleep(0.3)
        yield
        
        if len(value) >= 1:
            async with aiohttp.ClientSession() as session:
                results = await stock_api.search_stock_async(value, session)
                # 如果搜索结果为空，但用户输入了代码，创建一个无名称的结果项
                if not results and value.strip():
                    self.search_results = [{"code": value.strip(), "name": ""}]
                else:
                    self.search_results = results
        else:
            self.search_results = []
        yield

    def set_selected_stock(self, code: str, name: str):
        """设置当前选择的股票，用于单个添加"""
        # 只有当名称不为空时才设置
        if name and name.strip():
            self.add_stock_code = code
            self.add_stock_name = name
            self.selected_stocks = []  # 清空批量选择
            self.search_results = []  # 清空搜索结果

    def toggle_stock_selection(self, code: str, name: str):
        for stock in self.selected_stocks:
            if stock["code"] == code:
                self.selected_stocks = [s for s in self.selected_stocks if s["code"] != code]
                return
        self.selected_stocks = self.selected_stocks + [{"code": code, "name": name}]

    def clear_selection(self):
        self.selected_stocks = []

    async def add_to_watchlist(self):
        if not self.current_user_id:
            self.error_message = "请先登录"
            return
        if not self.add_stock_code:
            self.error_message = "请输入股票代码"
            return
        
        # 检查是否有搜索结果，如果没有则尝试搜索
        if not self.add_stock_name:
            async with aiohttp.ClientSession() as session:
                info = await stock_api.get_realtime_quote_async(self.add_stock_code.split(".")[0], session)
                if info and info.get("name"):
                    self.add_stock_name = info["name"]
                else:
                    self.error_message = "搜索不到该股票，请确认股票代码是否正确"
                    return
        
        try:
            item_repo = WatchlistItemRepository()
            code = self.add_stock_code.split(".")[0]
            if item_repo.item_exists(str(self.current_user_id), code):
                self.error_message = "已在自选股中"
                return
            name = self.add_stock_name
            
            item_repo.add_item(
                user_id=str(self.current_user_id),
                stock_code=code,
                stock_name=name
            )
            self.success_message = f"已添加 {name}"
            self.show_add_dialog = False
            
            new_item = {
                "id": "temp",
                "stock_code": code,
                "stock_name": name,
                "price": "--",
                "pct_chg": "--%",
                "currency": "¥",
                "market": _get_market(code)
            }
            self.watchlist_items = self.watchlist_items + [new_item]
            yield
            await self._do_refresh()
            yield
        except Exception as e:
            self.error_message = f"添加失败: {str(e)}"
            yield

    async def add_multiple_to_watchlist(self):
        if not self.current_user_id:
            self.error_message = "请先登录"
            return
        if not self.selected_stocks:
            self.error_message = "请选择股票"
            return
        try:
            item_repo = WatchlistItemRepository()
            added_count = 0
            new_items = []
            
            for stock in self.selected_stocks:
                code = stock["code"].split(".")[0]
                if not item_repo.item_exists(str(self.current_user_id), code):
                    item_repo.add_item(
                        user_id=str(self.current_user_id),
                        stock_code=code,
                        stock_name=stock.get("name", "")
                    )
                    new_items.append({
                        "id": "temp",
                        "stock_code": code,
                        "stock_name": stock.get("name", ""),
                        "price": "--",
                        "pct_chg": "--%",
                        "currency": "¥",
                        "market": _get_market(code)
                    })
                    added_count += 1
            
            self.success_message = f"已添加 {added_count} 只股票"
            self.selected_stocks = []
            self.show_add_dialog = False
            self.watchlist_items = self.watchlist_items + new_items
            await self._do_refresh()
        except Exception as e:
            self.error_message = f"添加失败: {str(e)}"

    async def remove_from_watchlist(self, item_id: str):
        try:
            item_repo = WatchlistItemRepository()
            item_repo.remove_item(item_id)
            self.success_message = "已删除"
            self.watchlist_items = [i for i in self.watchlist_items if i.get("id") != item_id]
            self._split_by_market()
            yield
        except Exception as e:
            self.error_message = f"删除失败: {str(e)}"
            yield
