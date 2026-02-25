# 用户自选股管理

## Summary

实现用户自选股管理功能，包括：
- 添加/删除自选股
- 自选股分组（科技股、金融股等）
- 实时价格展示
- K线图查看
- 股票详情页

## Motivation

用户需要一个地方管理自己关注的股票，这是量化交易平台的核心功能之一。用户登录后可以：
- 快速查看关注的股票价格变动
- 对股票进行分类管理
- 查看股票的历史走势和技术指标

## Approach

### 技术方案

1. **数据层**
   - 创建 `watchlist_items` 和 `watchlist_groups` 表
   - 创建 `WatchlistItem` 和 `WatchlistGroup` 模型类
   - 创建 Repository 类处理数据操作

2. **状态管理**
   - 创建 `WatchlistState` 继承 `AuthState`
   - 实现CRUD事件处理函数
   - 集成Tushare API获取股票数据

3. **UI层**
   - 自选股列表页
   - 添加/删除对话框
   - 分组管理界面
   - 股票详情页（含K线图）

### 依赖

- **Tushare**: 获取A股实时价格和历史数据
- **ECharts** (可选): 专业K线图展示

## Risks

1. **API调用限制**: Tushare免费版有每日调用限制
   - 缓解：本地缓存、批量请求

2. **代码量**: 可能超过300行
   - 缓解：模块拆分、代码复用

## Code Estimate

| 文件 | 代码行数 |
|------|----------|
| models.py (新增) | ~60行 |
| watchlist.py (state) | ~80行 |
| watchlist_pages.py | ~100行 |
| stock_api.py | ~50行 |
| db migration | ~30行 |
| **总计** | **~320行** |

## Alternatives Considered

### 方案A: 简洁版
- 只实现添加/删除/列表
- 不含K线图
- 代码量 ~200行

### 方案B: 完整版 (选择)
- 完整功能
- 代码量 ~320行

## Timeline

- 数据层实现: 30分钟
- 状态管理: 45分钟
- UI实现: 60分钟
- API集成: 30分钟
- 测试: 15分钟
- **总计: 约3小时**
