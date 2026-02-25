# 用户自选股管理设计

## Context

交易系统已完成用户认证功能，用户可以注册、登录、管理密码。但当前系统缺乏核心业务功能，用户无法管理自己关注的股票。

用户需要：
- 添加/删除自选股
- 对自选股进行分组管理
- 查看自选股实时价格和走势
- 查看股票详细信息和K线图

**约束条件**：
- 使用Reflex框架实现前后端一体化
- 数据库使用DuckDB
- 使用Tushare API获取股票数据
- 所有产出物必须用简体中文撰写

## Goals / Non-Goals

**Goals:**
1. 实现用户自选股的CRUD操作
2. 实现自选股分组功能
3. 集成Tushare API获取实时股价
4. 实现K线图展示
5. 实现股票详情查看

**Non-Goals:**
- 不实现交易下单功能
- 不实现策略回测（后续change）
- 不实现技术指标分析（后续change）
- 不实现股票推荐算法

## Decisions

### 1. 数据库设计

**决策**：创建 `watchlist_items` 和 `watchlist_groups` 表

```sql
CREATE TABLE watchlist_items (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    stock_code VARCHAR(20) NOT NULL,
    stock_name VARCHAR(100),
    group_id VARCHAR(36),
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (group_id) REFERENCES watchlist_groups(id),
    UNIQUE(user_id, stock_code)
);

CREATE TABLE watchlist_groups (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    name VARCHAR(50) NOT NULL,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE(user_id, name)
);
```

**理由**：支持分组功能，便于用户管理大量自选股

### 2. 股票数据API选择

**决策**：使用Tushare Pro API

**理由**：
- 数据质量高，更新及时
- 支持A股、港股、美股
- 提供丰富的财务数据
- 免费版有每日调用限制，适合个人项目

**配置**：
- 需要用户注册获取token
- 存储在 `.env` 文件中： `TUSHARE_TOKEN=xxx`

### 3. 状态管理

**决策**：创建 `WatchlistState` 继承 `AuthState`

```python
class WatchlistState(AuthState):
    watchlist_items: List[dict] = []
    groups: List[dict] = []
    selected_group: str = ""
    search_query: str = ""
    stock_detail: Optional[dict] = None
```

**理由**：继承认证状态，可直接访问 `current_user_id`

### 4. K线图实现

**决策**：使用Reflex内置图表组件或集成ECharts

**理由**：
- Reflex支持基础图表
- ECharts更专业，支持K线图
- 可渐进式集成

### 5. 页面路由

| 路由 | 页面 | 认证 |
|------|------|------|
| `/watchlist` | 自选股列表 | ✅ |
| `/watchlist/add` | 添加自选股 | ✅ |
| `/stock/{code}` | 股票详情 | ✅ |

## Specs

本change包含以下功能规格：

1. **watchlist-list** - 自选股列表展示
2. **watchlist-group** - 自选股分组管理
3. **stock-detail** - 股票详情和K线图

## Risks / Trade-offs

### 风险1：Tushare API调用限制

**风险**：免费版Tushare有每日调用次数限制

**缓解措施**：
- 实现本地缓存，避免重复请求
- 页面加载时批量获取数据
- 提示用户升级Pro版

### 风险2：代码量超过300行

**风险**：功能较完整，可能超过单功能300行限制

**缓解措施**：
- 按模块拆分代码文件
- 使用数据类减少重复代码
- K线图组件单独文件

### 风险3：实时数据更新

**风险**：股票价格需要实时更新

**缓解措施**：
- 初期使用手动刷新
- 后续可添加WebSocket推送

## Migration Plan

1. **数据库迁移**
   - 执行SQL创建watchlist表

2. **依赖安装**
   - `pip install tushare`

3. **配置更新**
   - 添加 `TUSHARE_TOKEN` 到 `.env`

4. **代码部署**
   - 创建models、state、pages
   - 更新路由配置
   - 添加导航入口
