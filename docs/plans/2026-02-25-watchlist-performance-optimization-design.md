# 自选股性能优化设计

## 问题概述

自选股功能存在严重的性能问题：
1. 刷新价格时 UI 完全冻结，数分钟才显示数据
2. 添加按钮无响应
3. 自选股面板无法关闭
4. 搜索无法获取真实股票名称

## 根因分析

**核心问题：同步阻塞**

`watchlist_state.py:59-73` 中 `refresh_prices()` 方法同步串行调用 `stock_api.get_realtime_quote()`，每只股票一次 HTTP 请求，阻塞 Reflex 事件循环，导致整个 UI 无响应。

## 解决方案

### 架构变更

**当前架构（阻塞）：**
```
UI Event → 同步 refresh_prices() → 串行 HTTP 请求 (阻塞) → UI 冻结
```

**优化后架构（非阻塞）：**
```
UI Event → @rx.background refresh_prices() → asyncio.gather(并行请求) → yield 更新 UI
```

### 变更范围

| 模块 | 变更内容 |
|------|----------|
| `stock_api.py` | 新增 `aiohttp` 异步方法 |
| `watchlist_state.py` | `@rx.background` 后台刷新 + 异步搜索防抖 |
| `watchlist_pages.py` | 多选 UI 组件 |
| `requirements.txt` | 添加 `aiohttp` |

**不变：** 数据库层、其他页面

## 详细设计

### 1. stock_api.py 变更

**新增依赖：**
```python
import aiohttp
import asyncio
```

**新增方法：**
```python
async def get_realtime_quote_async(self, stock_code: str, session: aiohttp.ClientSession) -> Optional[Dict]:
    """异步获取实时行情"""
    secid = self._get_secid(stock_code)
    url = f"https://push2.eastmoney.com/api/qt/stock/get?secid={secid}&fields=f43,f44,f45,f46,f47,f48,f50,f51,f52,f55,f57,f58,f60"
    
    try:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
            data = await response.json()
            # 解析逻辑复用现有代码
            return self._parse_quote_data(data, stock_code)
    except Exception as e:
        print(f"异步请求失败: {e}")
        return None

async def search_stock_async(self, keyword: str, session: aiohttp.ClientSession) -> List[Dict]:
    """异步搜索股票，返回真实名称"""
    # 调用东方财富搜索 API
    url = f"https://searchapi.eastmoney.com/bussiness/web/QuotationLabelSearch?keyword={keyword}"
    # 解析返回真实名称
```

### 2. watchlist_state.py 变更

**新增状态变量：**
```python
selected_stocks: List[dict] = []  # 多选的股票列表
search_debounce_task: Optional[asyncio.Task] = None  # 防抖任务
```

**刷新价格改为后台异步：**
```python
@rx.background
async def refresh_prices(self):
    if not self.watchlist_items:
        return
    
    async with self.get_state(WatchlistState) as state:
        state.is_loading = True
        yield state
    
    async with aiohttp.ClientSession() as session:
        codes = [item.get('stock_code', '') for item in self.watchlist_items]
        tasks = [stock_api.get_realtime_quote_async(code, session) for code in codes]
        results = await asyncio.gather(*tasks, return_exceptions=True)
    
    async with self.get_state(WatchlistState) as state:
        for i, result in enumerate(results):
            if isinstance(result, dict) and result:
                state.watchlist_items[i].update({
                    'price': result.get('price', 0),
                    'pct_chg': result.get('pct_chg', 0),
                    'change': result.get('change', 0),
                    'currency': result.get('currency', '¥'),
                    'stock_name': result.get('name', state.watchlist_items[i].get('stock_name', ''))
                })
        state.is_loading = False
        state.last_refresh_time = datetime.now().strftime("%H:%M:%S")
        state.success_message = "刷新成功"
        yield state
```

**搜索防抖：**
```python
async def search_with_debounce(self, value: str):
    """防抖搜索"""
    if self.search_debounce_task:
        self.search_debounce_task.cancel()
    
    async def do_search():
        await asyncio.sleep(0.3)  # 300ms 防抖
        if len(value) >= 1:
            async with aiohttp.ClientSession() as session:
                results = await stock_api.search_stock_async(value, session)
                async with self.get_state(WatchlistState) as state:
                    state.search_results = results
                    yield state
    
    self.search_debounce_task = asyncio.create_task(do_search())
```

**多选支持：**
```python
def toggle_stock_selection(self, code: str, name: str):
    """切换股票选择状态"""
    for stock in self.selected_stocks:
        if stock['code'] == code:
            self.selected_stocks = [s for s in self.selected_stocks if s['code'] != code]
            return
    self.selected_stocks.append({'code': code, 'name': name})

def parse_multiple_codes(self, input_str: str) -> List[str]:
    """解析逗号分隔的股票代码"""
    codes = [c.strip() for c in input_str.replace('，', ',').split(',') if c.strip()]
    return codes

async def add_multiple_to_watchlist(self):
    """批量添加自选股"""
    # 遍历 selected_stocks 批量添加
```

### 3. watchlist_pages.py 变更

**多选 UI：**
- 搜索结果每项增加复选框
- 底部显示已选数量和批量添加按钮
- 输入框支持逗号分隔多代码

### 4. requirements.txt

```
aiohttp>=3.9.0
```

## 数据流

### 刷新价格流程
```
用户点击"刷新" 
  → refresh_prices() 后台启动 
  → is_loading=True (显示 spinner) 
  → asyncio.gather 并行请求所有股票 
  → 一次性更新 watchlist_items 
  → is_loading=False (显示结果)
```

### 搜索添加流程
```
用户输入 
  → 300ms 防抖 
  → 异步搜索 API 
  → 显示结果(带复选框/真实名称) 
  → 勾选多个/逗号分隔 
  → 批量添加
```

## 错误处理

1. 单只股票请求失败不影响其他股票
2. `return_exceptions=True` 捕获异常继续执行
3. 超时设置：单请求 5 秒
4. 断网时显示友好错误提示

## 测试验证

1. 添加 10-30 只股票，点击刷新，验证 3 秒内完成
2. 刷新期间点击其他按钮，验证 UI 不卡顿
3. 搜索输入，验证 300ms 后才发起请求
4. 多选添加，验证批量添加成功
5. 断网测试，验证错误处理不崩溃

## 风险与缓解

| 风险 | 缓解措施 |
|------|----------|
| aiohttp 与现有 urllib 冲突 | 保留同步方法，两套 API 共存 |
| 东方财富 API 限流 | 并发控制，最多 30 个并行 |
| 搜索 API 响应慢 | 防抖 + 加载状态提示 |

## 不变的部分

- 数据库操作保持同步
- models.py 无需修改
- 其他页面（dashboard_pages.py, pages.py）无需修改
