# 自选股性能优化实现计划

## 概述

基于设计文档 `2026-02-25-watchlist-performance-optimization-design.md`，本计划将同步阻塞的 HTTP 请求重构为异步非阻塞架构。

---

## 任务清单

### 阶段 1：基础设施（依赖 + 异步 API）

#### 任务 1.1：添加 aiohttp 依赖

**文件：** `requirements.txt`

**变更：**
```
+ aiohttp>=3.9.0
```

**验证：**
```bash
pip install -r requirements.txt
python -c "import aiohttp; print(aiohttp.__version__)"
```

---

#### 任务 1.2：新增异步行情方法

**文件：** `stock_api.py`

**变更点：**
1. 文件顶部添加导入：
   ```python
   import aiohttp
   import asyncio
   ```

2. 在 `get_realtime_quote()` 方法后新增：
   ```python
   async def get_realtime_quote_async(self, stock_code: str, session: aiohttp.ClientSession) -> Optional[Dict]:
       """异步获取实时行情"""
       secid = self._get_secid(stock_code)
       is_hk = self._is_hk_stock(stock_code)
       is_us = self._is_us_stock(stock_code)
       divisor = 1000 if is_hk else 100
       currency = "HK$" if is_hk else "$" if is_us else "¥"
       
       url = f"https://push2.eastmoney.com/api/qt/stock/get?secid={secid}&fields=f43,f44,f45,f46,f47,f48,f50,f51,f52,f55,f57,f58,f60"
       
       try:
           async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
               data = await response.json()
               if not data or 'data' not in data or not data['data']:
                   return None
               d = data['data']
               price = d.get('f43', 0) / divisor if d.get('f43') else 0
               pre_close = d.get('f60', 0) / divisor if d.get('f60') else 0
               change = price - pre_close if pre_close > 0 else 0
               pct_chg = (change / pre_close * 100) if pre_close > 0 else 0
               return {
                   "code": str(d.get('f57', '')),
                   "name": d.get('f58', ''),
                   "price": round(price, 2),
                   "pre_close": round(pre_close, 2),
                   "change": round(change, 2),
                   "pct_chg": round(pct_chg, 2),
                   "currency": currency
               }
       except Exception as e:
           print(f"异步请求失败 [{stock_code}]: {e}")
           return None
   ```

**验证：**
```python
# 测试脚本
import asyncio
import aiohttp
from stock_api import stock_api

async def test():
    async with aiohttp.ClientSession() as session:
        result = await stock_api.get_realtime_quote_async("600519", session)
        print(result)

asyncio.run(test())
```

---

#### 任务 1.3：新增异步搜索方法

**文件：** `stock_api.py`

**变更点：**
1. 在 `search_stock()` 方法后新增：
   ```python
   async def search_stock_async(self, keyword: str, session: aiohttp.ClientSession) -> List[Dict]:
       """异步搜索股票，返回真实名称"""
       results = []
       
       # 构建本地结果（保持原有逻辑）
       keyword = keyword.upper()
       if keyword.isdigit() and len(keyword) <= 5:
           code = keyword.zfill(5)
           results.append({"code": f"{code}.HK", "name": f"港股{code}", "market": "HK"})
       if keyword.isdigit() and len(keyword) <= 6:
           code = keyword.zfill(6)
           market = "SH" if code.startswith('6') else "SZ"
           results.append({"code": f"{code}.{market}", "name": f"A股{code}", "market": market})
       if keyword.isalpha():
           results.append({"code": keyword, "name": keyword, "market": "US"})
       
       # 尝试获取真实名称
       try:
           url = f"https://searchapi.eastmoney.com/bussiness/web/QuotationLabelSearch?keyword={keyword}"
           headers = {
               'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
               'Referer': 'https://quote.eastmoney.com/'
           }
           async with session.get(url, timeout=aiohttp.ClientTimeout(total=3), headers=headers) as response:
               data = await response.json()
               if data and 'Data' in data:
                   for item in data['Data'][:5]:
                       code = item.get('Code', '')
                       name = item.get('Name', '')
                       market_code = item.get('MktNum', '')
                       if code and name:
                           market = 'HK' if market_code == '116' else 'SH' if market_code == '1' else 'SZ'
                           results.append({"code": f"{code}.{market}", "name": name, "market": market})
       except Exception as e:
           print(f"搜索API失败: {e}")
       
       return results[:5]
   ```

**验证：**
```python
import asyncio
import aiohttp
from stock_api import stock_api

async def test():
    async with aiohttp.ClientSession() as session:
        results = await stock_api.search_stock_async("茅台", session)
        print(results)

asyncio.run(test())
```

---

### 阶段 2：状态层重构（核心变更）

#### 任务 2.1：添加新状态变量

**文件：** `watchlist_state.py`

**变更点：**
1. 添加导入：
   ```python
   import aiohttp
   import asyncio
   from typing import Optional
   ```

2. 在类属性中添加（约第 28 行后）：
   ```python
   selected_stocks: List[dict] = []
   search_debounce_task: Optional[asyncio.Task] = None
   ```

**验证：** 应用启动无报错

---

#### 任务 2.2：重构 refresh_prices 为异步后台任务

**文件：** `watchlist_state.py`

**变更点：** 替换原有 `refresh_prices()` 方法（第 53-81 行）：

```python
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
```

**关键点：**
- `@rx.background` 装饰器：方法在后台执行
- `async with self.get_state()` + `yield`：安全更新状态
- `asyncio.gather(*tasks)`：并行请求
- `return_exceptions=True`：单只股票失败不影响其他

**验证：**
1. 添加 5-10 只股票
2. 点击刷新，观察 UI 是否仍可操作
3. 检查控制台无异常

---

#### 任务 2.3：添加搜索防抖方法

**文件：** `watchlist_state.py`

**变更点：** 在 `set_add_stock_code()` 方法后添加：

```python
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
                    state.search_results = results
                    yield state
    
    self.search_debounce_task = asyncio.create_task(do_search())
```

**验证：**
1. 快速输入多个字符
2. 确认只在停止输入 300ms 后发起请求

---

#### 任务 2.4：添加多选支持方法

**文件：** `watchlist_state.py`

**变更点：** 添加以下方法：

```python
def toggle_stock_selection(self, code: str, name: str):
    """切换股票选择状态"""
    for stock in self.selected_stocks:
        if stock['code'] == code:
            self.selected_stocks = [s for s in self.selected_stocks if s['code'] != code]
            return
    self.selected_stocks.append({'code': code, 'name': name})

def clear_selection(self):
    """清空选择"""
    self.selected_stocks = []

def parse_multiple_codes(self, input_str: str) -> List[str]:
    """解析逗号分隔的股票代码"""
    codes = [c.strip() for c in input_str.replace('，', ',').split(',') if c.strip()]
    return codes

async def add_multiple_to_watchlist(self):
    """批量添加自选股"""
    if not self.current_user_id:
        self.error_message = "请先登录"
        return
    
    if not self.selected_stocks:
        self.error_message = "请选择股票"
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
        
        self.success_message = f"已添加 {added_count} 只股票"
        self.selected_stocks = []
        self.show_add_dialog = False
        self.load_watchlist()
    except Exception as e:
        self.error_message = f"添加失败: {str(e)}"
```

**验证：**
1. 选择多只股票
2. 批量添加成功
3. 重复股票不重复添加

---

### 阶段 3：UI 层更新

#### 任务 3.1：更新搜索触发方式

**文件：** `watchlist_pages.py`

**变更点：** 修改 `_add_dialog()` 中的 input 组件：

```python
rx.input(
    placeholder="股票代码 (如 600519, 09988, AAPL)",
    value=WatchlistState.add_stock_code,
    on_change=WatchlistState.search_with_debounce,  # 改为防抖搜索
    width="100%"
)
```

**验证：** 输入时无卡顿

---

#### 任务 3.2：添加多选 UI 组件

**文件：** `watchlist_pages.py`

**变更点：**

1. 修改 `_search_result_item()` 函数，添加复选框：

```python
def _search_result_item(item: dict) -> rx.Component:
    is_selected = WatchlistState.selected_stocks.contains(
        lambda s: s['code'] == item.get('code', '')
    )
    return rx.box(
        rx.hstack(
            rx.checkbox(
                checked=WatchlistState.selected_stocks.contains(
                    lambda s, code=item.get('code', ''): s['code'] == code
                ),
                on_change=lambda: WatchlistState.toggle_stock_selection(
                    item.get('code', ''), item.get('name', '')
                )
            ),
            rx.text(item.get('code', ''), color=TECH_COLORS['primary'], width='80px'),
            rx.text(item.get('name', ''), color=TECH_COLORS['light']),
            width='100%'
        ),
        padding='8px 12px',
        cursor='pointer',
        on_click=lambda: WatchlistState.toggle_stock_selection(
            item.get('code', ''), item.get('name', '')
        ),
        _hover={'bg': 'rgba(255,255,255,0.1)'},
        width='100%'
    )
```

2. 修改 `_add_dialog()` 底部，添加批量添加按钮：

```python
# 替换原有的底部按钮区域
rx.cond(
    WatchlistState.selected_stocks.length() > 0,
    rx.hstack(
        rx.text(f"已选 {WatchlistState.selected_stocks.length()} 只", color='#888'),
        rx.spacer(),
        rx.button('清空', on_click=WatchlistState.clear_selection, variant='outline'),
        rx.button('批量添加', on_click=WatchlistState.add_multiple_to_watchlist, color_scheme='blue'),
        spacing='2'
    ),
    rx.hstack(
        rx.button('取消', on_click=WatchlistState.close_add_dialog, variant='outline'),
        rx.button('添加单个', on_click=WatchlistState.add_to_watchlist, color_scheme='blue'),
        spacing='2'
    )
)
```

**验证：**
1. 搜索结果可多选
2. 显示已选数量
3. 批量添加成功

---

### 阶段 4：集成测试

#### 任务 4.1：端到端功能验证

**测试步骤：**

| 测试项 | 操作 | 预期结果 |
|--------|------|----------|
| 刷新性能 | 添加 20 只股票，点击刷新 | 3 秒内完成，UI 不卡顿 |
| 刷新期间操作 | 刷新期间点击其他按钮 | 按钮响应正常 |
| 搜索防抖 | 快速连续输入 | 停止输入 300ms 后才搜索 |
| 多选添加 | 勾选 5 只股票，批量添加 | 5 只全部添加成功 |
| 单只失败 | 删除一只股票的行情数据 | 其他股票正常刷新 |
| 断网测试 | 断开网络后刷新 | 显示友好错误，不崩溃 |

**命令：**
```bash
reflex run
# 打开浏览器访问 http://localhost:3000/watchlist
```

---

#### 任务 4.2：性能基准

**指标：**
- 10 只股票刷新 < 2 秒
- 30 只股票刷新 < 5 秒
- 刷新期间 UI 响应延迟 < 100ms

**验证方式：** 浏览器 DevTools Network 面板 + Performance 面板

---

## 文件变更汇总

| 文件 | 变更类型 | 关键变更 |
|------|----------|----------|
| `requirements.txt` | 新增依赖 | +aiohttp>=3.9.0 |
| `stock_api.py` | 新增方法 | +get_realtime_quote_async(), +search_stock_async() |
| `watchlist_state.py` | 重构+新增 | @rx.background refresh_prices(), 多选方法 |
| `watchlist_pages.py` | UI 更新 | 复选框、批量添加按钮 |

---

## 执行顺序

```
1.1 → 1.2 → 1.3 → 2.1 → 2.2 → 2.3 → 2.4 → 3.1 → 3.2 → 4.1 → 4.2
```

**关键路径：** 1.2 → 2.2（异步行情是核心变更）

---

## 回滚方案

如遇问题，回滚步骤：

1. 恢复 `watchlist_state.py` 中的 `refresh_prices()` 为同步版本
2. 移除 `@rx.background` 装饰器
3. 删除 `aiohttp` 相关代码

---

## 注意事项

1. **Reflex 状态更新规则：** 后台任务必须使用 `async with self.get_state()` + `yield`
2. **并发控制：** 建议限制最多 30 个并行请求
3. **错误隔离：** 单只股票失败不应影响整体刷新
4. **保留同步方法：** `get_realtime_quote()` 保持不变，供其他模块使用
