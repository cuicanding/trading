# 美港股支持增强实施计划

> **for Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 巻加完整的美港股指数数据支持，并优化美股搜索功能

**Architecture:** 扩展现有东方财富API的secid配置，并优化前端展示布局，支持分市场展示指数
**Tech Stack:** 
- Python 3.11+ (Reflex)
- DuckDB
- aiohttp (API请求)
- 东方财富API (数据源)

- JavaScript (前端定时器)

## Plan Document Header
Every plan must start with this header:

```markdown
# [美港股支持增强] Implementation Plan
> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 添加完整的美港股指数数据支持,并优化美股搜索功能
**Architecture:** 扩展现有东方财富API的secid配置，并优化前端展示布局，支持分市场展示指数
**Tech Stack:** 
- Python 3.11+ (Reflex)
- DuckDB
- aiohttp (API请求)
- 东方财富API (数据源)
- JavaScript (前端定时器)

---
```

## Task Structure

### Task 1: 扩展指数配置
**Files:**
- Create: `stock_api.py` (添加更多指数配置)
- Test: `tests/test_index_quotes.py`

**Step 1: 编写失败的测试**

```python
def test_index_quotes():
    """测试获取指数数据"""
    api = StockAPI()
    quotes = api.get_index_quotes()
    assert len(quotes) >= 6  # 现在应该支持6个指数
    assert any(q["name"] == "恒生指数" for q in quotes)
    assert any(q["name"] == "纳斯达克" for q in quotes)
```

**Step 2: 运行测试验证失败**

```bash
pytest tests/test_index_quotes.py::test_index_quotes -v
# 预期: FAIL - 指数数量不足
```
**Step 3: 编写最小实现**

```python
# 在 stock_api.py 中
INDEX_CONFIG = {
    # A股指数
    "sh": {"secid": "1.000001", "name": "上证指数", "currency": "¥"},
    "sz": {"secid": "0.399001", "name": "深证成指", "currency": "¥"},
    
    # 港股指数
    "hsi": {"secid": "100.HSI", "name": "恒生指数", "currency": "HK$"},
    "hstech": {"secid": "100.HSTECH", "name": "恒生科技", "currency": "HK$"},
    
    # 美股指数
    "ixic": {"secid": "100.IXIC", "name": "纳斯达克", "currency": "$"},
    "dji": {"secid": "100.DJI", "name": "道琼斯", "currency": "$"},
    "sp500": {"secid": "100.SPX", "name": "标普500", "currency": "$"},
}
```
**Step 4: 运行测试验证通过**

```bash
pytest tests/test_index_quotes.py::test_index_quotes -v
# 预期: PASS - 所有指数都能正确获取
```
**Step 5: 提交**

```bash
git add stock_api.py
git commit -m "feat: 添加港股和美股指数支持"
```

### Task 2: 优化前端展示
**Files:**
- Modify: `watchlist_pages.py` (修改指数展示布局)
- Test: `tests/test_ui.py`

**Step 1: 编写失败的测试**

```python
def test_index_display():
    """测试指数展示布局"""
    # 应该有3个独立的区块
    assert has_a_stock_index_section()
    assert has_hk_index_section()
    assert has_us_index_section()
```
**Step 2: 运行测试验证失败**

```bash
pytest tests/test_ui.py::test_index_display -v
# 预期: FAIL - 只有2个区块
```
**Step 3: 编写最小实现**

```python
# 在 watchlist_pages.py 中
def _index_bar():
    return rx.hstack(
        _a_stock_index_block(),
        _hk_index_block(),
        _us_index_block(),
        spacing="2",
        width="100%"
    )

def _a_stock_index_block():
    indices = [q for q in WatchlistState.index_quotes if q.get("market") == "A"]
    return rx.hstack(
        rx.foreach(indices, _index_item),
        spacing="1"
    )

# 类似的函数用于港股和美股区块
```
**Step 4: 运行测试验证通过**

```bash
pytest tests/test_ui.py::test_index_display -v
# 预期: PASS - 三个区块正确显示
```
**Step 5: 提交**

```bash
git add watchlist_pages.py
git commit -m "feat: 优化指数展示布局，```
