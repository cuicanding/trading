# 用户自选股管理实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 实现用户自选股管理功能：添加/删除/分组/查看股票详情

**Architecture:** 
1. 数据层：创建WatchlistItem/Group模型和Repository
2. API层：集成Tushare获取股票数据
3. 状态层：WatchlistState管理自选股操作
4. UI层：自选股列表页 + 股票详情页

**Tech Stack:** Python, Reflex, DuckDB, Tushare

---

## Task 1: 数据库设置

**Files:**
- Modify: `db_init.py`

### Step 1: 添加自选股表到db_init.py

```python
# 在 db_init.py 中添加以下表定义

# 自选股分组表
conn.execute("""
    CREATE TABLE IF NOT EXISTS watchlist_groups (
        id VARCHAR(36) PRIMARY KEY,
        user_id VARCHAR(36) NOT NULL,
        name VARCHAR(50) NOT NULL,
        sort_order INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id),
        UNIQUE(user_id, name)
    )
""")

# 自选股项目表
conn.execute("""
    CREATE TABLE IF NOT EXISTS watchlist_items (
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
    )
""")

# 创建索引
conn.execute("CREATE INDEX IF NOT EXISTS idx_watchlist_user ON watchlist_items(user_id)")
conn.execute("CREATE INDEX IF NOT EXISTS idx_watchlist_group ON watchlist_items(group_id)")
conn.execute("CREATE INDEX IF NOT EXISTS idx_watchlist_code ON watchlist_items(stock_code)")
```

### Step 2: 运行数据库初始化

Run: `python db_init.py`
Expected: 表创建成功

---

## Task 2: 依赖项安装

**Files:**
- Modify: `requirements.txt`
- Modify: `.env.example`

### Step 1: 安装Tushare

```bash
pip install tushare
```

### Step 2: 更新requirements.txt

```
tushare
```

### Step 3: 更新.env.example

```
TUSHARE_TOKEN=your_tushare_token_here
```

---

## Task 3: 数据模型实现

**Files:**
- Modify: `models.py`

### Step 1: 添加WatchlistGroup模型

```python
class WatchlistGroup:
    """自选股分组模型"""
    
    def __init__(
        self,
        id: str,
        user_id: str,
        name: str,
        sort_order: int = 0,
        created_at: Optional[datetime] = None
    ):
        self.id = id
        self.user_id = user_id
        self.name = name
        self.sort_order = sort_order
        self.created_at = created_at or datetime.now()
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "sort_order": self.sort_order,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
```

### Step 2: 添加WatchlistItem模型

```python
class WatchlistItem:
    """自选股项目模型"""
    
    def __init__(
        self,
        id: str,
        user_id: str,
        stock_code: str,
        stock_name: str = "",
        group_id: Optional[str] = None,
        sort_order: int = 0,
        created_at: Optional[datetime] = None
    ):
        self.id = id
        self.user_id = user_id
        self.stock_code = stock_code
        self.stock_name = stock_name
        self.group_id = group_id
        self.sort_order = sort_order
        self.created_at = created_at or datetime.now()
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "stock_code": self.stock_code,
            "stock_name": self.stock_name,
            "group_id": self.group_id,
            "sort_order": self.sort_order,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
```

### Step 3: 添加WatchlistGroupRepository

```python
class WatchlistGroupRepository:
    """自选股分组Repository"""
    
    def __init__(self, db_path: str = "trading.db"):
        self.db_path = db_path
        self.conn = None
    
    def connect(self):
        if self.conn is None:
            self.conn = duckdb.connect(self.db_path)
        return self.conn
    
    def create_group(self, user_id: str, name: str) -> WatchlistGroup:
        self.connect()
        group_id = str(uuid.uuid4())
        self.conn.execute(
            "INSERT INTO watchlist_groups (id, user_id, name) VALUES (?, ?, ?)",
            [group_id, user_id, name]
        )
        return WatchlistGroup(id=group_id, user_id=user_id, name=name)
    
    def get_groups_by_user(self, user_id: str) -> List[WatchlistGroup]:
        self.connect()
        results = self.conn.execute(
            "SELECT * FROM watchlist_groups WHERE user_id = ? ORDER BY sort_order, created_at",
            [user_id]
        ).fetchall()
        return [WatchlistGroup(
            id=r[0], user_id=r[1], name=r[2], 
            sort_order=r[3], created_at=r[4]
        ) for r in results]
    
    def delete_group(self, group_id: str):
        self.connect()
        self.conn.execute("DELETE FROM watchlist_groups WHERE id = ?", [group_id])
```

### Step 4: 添加WatchlistItemRepository

```python
class WatchlistItemRepository:
    """自选股项目Repository"""
    
    def __init__(self, db_path: str = "trading.db"):
        self.db_path = db_path
        self.conn = None
    
    def connect(self):
        if self.conn is None:
            self.conn = duckdb.connect(self.db_path)
        return self.conn
    
    def add_item(self, user_id: str, stock_code: str, stock_name: str, group_id: Optional[str] = None) -> WatchlistItem:
        self.connect()
        item_id = str(uuid.uuid4())
        self.conn.execute(
            "INSERT INTO watchlist_items (id, user_id, stock_code, stock_name, group_id) VALUES (?, ?, ?, ?, ?)",
            [item_id, user_id, stock_code, stock_name, group_id]
        )
        return WatchlistItem(
            id=item_id, user_id=user_id, stock_code=stock_code, 
            stock_name=stock_name, group_id=group_id
        )
    
    def get_items_by_user(self, user_id: str, group_id: Optional[str] = None) -> List[WatchlistItem]:
        self.connect()
        if group_id:
            results = self.conn.execute(
                "SELECT * FROM watchlist_items WHERE user_id = ? AND group_id = ? ORDER BY sort_order, created_at",
                [user_id, group_id]
            ).fetchall()
        else:
            results = self.conn.execute(
                "SELECT * FROM watchlist_items WHERE user_id = ? ORDER BY sort_order, created_at",
                [user_id]
            ).fetchall()
        return [WatchlistItem(
            id=r[0], user_id=r[1], stock_code=r[2], stock_name=r[3],
            group_id=r[4], sort_order=r[5], created_at=r[6]
        ) for r in results]
    
    def remove_item(self, item_id: str):
        self.connect()
        self.conn.execute("DELETE FROM watchlist_items WHERE id = ?", [item_id])
    
    def item_exists(self, user_id: str, stock_code: str) -> bool:
        self.connect()
        result = self.conn.execute(
            "SELECT COUNT(*) FROM watchlist_items WHERE user_id = ? AND stock_code = ?",
            [user_id, stock_code]
        ).fetchone()
        return result[0] > 0
```

---

## Task 4: 股票数据API

**Files:**
- Create: `stock_api.py`

### Step 1: 创建stock_api.py

```python
"""
股票数据API
使用Tushare获取股票数据
"""
import tushare as ts
from typing import Optional, List, Dict
from config import Config

class StockAPI:
    def __init__(self):
        self.pro = ts.pro_api(Config.TUSHARE_TOKEN) if Config.TUSHARE_TOKEN else None
    
    def is_configured(self) -> bool:
        return self.pro is not None
    
    def get_stock_info(self, stock_code: str) -> Optional[Dict]:
        """获取股票基本信息"""
        if not self.is_configured():
            return None
        try:
            # 去掉后缀 (.SH/.SZ)
            code = stock_code.split('.')[0]
            df = self.pro.stock_basic(ts_code=stock_code, fields='ts_code,name,industry,market')
            if df.empty:
                return None
            row = df.iloc[0]
            return {
                "code": row['ts_code'],
                "name": row['name'],
                "industry": row['industry'],
                "market": row['market']
            }
        except Exception as e:
            print(f"获取股票信息失败: {e}")
            return None
    
    def get_realtime_quote(self, stock_code: str) -> Optional[Dict]:
        """获取实时行情"""
        if not self.is_configured():
            return None
        try:
            df = self.pro.realtime_quote(ts_code=stock_code)
            if df.empty:
                return None
            row = df.iloc[0]
            return {
                "code": row['ts_code'],
                "name": row['name'],
                "price": float(row['price']),
                "change": float(row['change']),
                "pct_chg": float(row['pct_chg']),
                "volume": float(row['volume']),
                "amount": float(row['amount'])
            }
        except Exception as e:
            print(f"获取实时行情失败: {e}")
            return None
    
    def get_daily_kline(self, stock_code: str, days: int = 60) -> List[Dict]:
        """获取日K线数据"""
        if not self.is_configured():
            return []
        try:
            df = self.pro.daily(ts_code=stock_code, limit=days)
            if df.empty:
                return []
            return [
                {
                    "date": row['trade_date'],
                    "open": float(row['open']),
                    "high": float(row['high']),
                    "low": float(row['low']),
                    "close": float(row['close']),
                    "volume": float(row['vol']),
                    "amount": float(row['amount'])
                }
                for _, row in df.iterrows()
            ]
        except Exception as e:
            print(f"获取K线数据失败: {e}")
            return []

stock_api = StockAPI()
```

---

## Task 5: 自选股状态管理

**Files:**
- Create: `watchlist_state.py`

### Step 1: 创建watchlist_state.py

```python
"""
自选股状态管理
"""
import reflex as rx
from typing import Optional, List
from auth import AuthState
from models import WatchlistItem, WatchlistGroup, WatchlistItemRepository, WatchlistGroupRepository
from stock_api import stock_api

class WatchlistState(AuthState):
    """自选股状态"""
    
    watchlist_items: List[dict] = []
    groups: List[dict] = []
    selected_group: str = ""
    search_query: str = ""
    is_loading: bool = False
    error_message: str = ""
    success_message: str = ""
    
    # 添加自选股相关
    add_stock_code: str = ""
    add_stock_name: str = ""
    show_add_dialog: bool = False
    
    def load_watchlist(self):
        """加载自选股列表"""
        if not self.current_user_id:
            return
        self.is_loading = True
        try:
            item_repo = WatchlistItemRepository()
            group_repo = WatchlistGroupRepository()
            
            # 获取分组
            self.groups = [g.to_dict() for g in group_repo.get_groups_by_user(self.current_user_id)]
            
            # 获取自选股
            items = item_repo.get_items_by_user(
                self.current_user_id, 
                self.selected_group if self.selected_group else None
            )
            
            # 获取实时价格
            result = []
            for item in items:
                item_dict = item.to_dict()
                quote = stock_api.get_realtime_quote(item.stock_code)
                if quote:
                    item_dict.update(quote)
                result.append(item_dict)
            
            self.watchlist_items = result
        except Exception as e:
            self.error_message = f"加载失败: {str(e)}"
        finally:
            self.is_loading = False
    
    def add_to_watchlist(self):
        """添加股票到自选股"""
        if not self.current_user_id:
            return
        if not self.add_stock_code:
            self.error_message = "请输入股票代码"
            return
        
        self.is_loading = True
        try:
            item_repo = WatchlistItemRepository()
            
            # 检查是否已存在
            if item_repo.item_exists(self.current_user_id, self.add_stock_code):
                self.error_message = "该股票已在自选股中"
                return
            
            # 获取股票名称
            stock_info = stock_api.get_stock_info(self.add_stock_code)
            stock_name = stock_info['name'] if stock_info else self.add_stock_name
            
            # 添加到数据库
            item_repo.add_item(
                user_id=self.current_user_id,
                stock_code=self.add_stock_code,
                stock_name=stock_name or "",
                group_id=self.selected_group if self.selected_group else None
            )
            
            self.success_message = "添加成功"
            self.show_add_dialog = False
            self.add_stock_code = ""
            self.add_stock_name = ""
            self.load_watchlist()
        except Exception as e:
            self.error_message = f"添加失败: {str(e)}"
        finally:
            self.is_loading = False
    
    def remove_from_watchlist(self, item_id: str):
        """从自选股移除"""
        self.is_loading = True
        try:
            item_repo = WatchlistItemRepository()
            item_repo.remove_item(item_id)
            self.success_message = "移除成功"
            self.load_watchlist()
        except Exception as e:
            self.error_message = f"移除失败: {str(e)}"
        finally:
            self.is_loading = False
    
    def create_group(self, name: str):
        """创建分组"""
        if not self.current_user_id:
            return
        try:
            group_repo = WatchlistGroupRepository()
            group_repo.create_group(self.current_user_id, name)
            self.success_message = "分组创建成功"
            self.load_watchlist()
        except Exception as e:
            self.error_message = f"创建失败: {str(e)}"
    
    def select_group(self, group_id: str):
        """选择分组"""
        self.selected_group = group_id
        self.load_watchlist()
    
    def clear_messages(self):
        """清除消息"""
        self.error_message = ""
        self.success_message = ""
```

---

## Task 6: 自选股列表页面

**Files:**
- Create: `watchlist_pages.py`

### Step 1: 创建watchlist_pages.py

```python
"""
自选股页面组件
"""
import reflex as rx
from watchlist_state import WatchlistState

TECH_COLORS = {
    "primary": "#00f0ff",
    "secondary": "#7000ff",
    "accent": "#ff00aa",
    "dark": "#0a0a0f",
    "darker": "#050508",
    "light": "#ffffff",
    "gray": "#2a2a35",
    "success": "#00ff88",
    "error": "#ff3366"
}

def tech_background() -> rx.Component:
    return rx.box(
        position="fixed", top="0", left="0", right="0", bottom="0",
        bg=TECH_COLORS["darker"], z_index="-2"
    )

def watchlist_page() -> rx.Component:
    """自选股列表页面"""
    return rx.box(
        tech_background(),
        rx.vstack(
            # 顶部栏
            rx.hstack(
                rx.heading("我的自选股", size="7", color=TECH_COLORS["light"]),
                rx.spacer(),
                rx.button(
                    "+ 添加",
                    on_click=WatchlistState.set_show_add_dialog(True),
                    bg=f"linear-gradient(135deg, {TECH_COLORS['primary']}, {TECH_COLORS['secondary']})",
                    color=TECH_COLORS["dark"],
                    border_radius="8px"
                ),
                width="100%",
                padding="20px"
            ),
            
            # 分组标签
            rx.hstack(
                rx.button(
                    "全部",
                    on_click=WatchlistState.select_group(""),
                    variant="outline" if WatchlistState.selected_group else "solid"
                ),
                rx.foreach(
                    WatchlistState.groups,
                    lambda g: rx.button(
                        g["name"],
                        on_click=WatchlistState.select_group(g["id"]),
                        variant="outline" if WatchlistState.selected_group != g["id"] else "solid"
                    )
                ),
                spacing="2",
                padding_x="20px"
            ),
            
            # 消息提示
            rx.cond(
                WatchlistState.error_message != "",
                rx.box(WatchlistState.error_message, color=TECH_COLORS["error"], padding="10px")
            ),
            rx.cond(
                WatchlistState.success_message != "",
                rx.box(WatchlistState.success_message, color=TECH_COLORS["success"], padding="10px")
            ),
            
            # 自选股列表
            rx.cond(
                WatchlistState.is_loading,
                rx.spinner(),
                rx.box(
                    rx.foreach(
                        WatchlistState.watchlist_items,
                        lambda item: rx.box(
                            rx.hstack(
                                rx.vstack(
                                    rx.text(item["stock_code"], font_weight="bold", color=TECH_COLORS["light"]),
                                    rx.text(item["stock_name"], color="#888"),
                                    spacing="1"
                                ),
                                rx.spacer(),
                                rx.vstack(
                                    rx.text(f"¥{item.get('price', '--')}", font_size="18px", color=TECH_COLORS["light"]),
                                    rx.text(
                                        f"{item.get('pct_chg', 0):+.2f}%",
                                        color=TECH_COLORS["success"] if item.get('pct_chg', 0) >= 0 else TECH_COLORS["error"]
                                    ),
                                    align_items="end"
                                ),
                                rx.button(
                                    "删除",
                                    on_click=WatchlistState.remove_from_watchlist(item["id"]),
                                    variant="ghost",
                                    color=TECH_COLORS["error"]
                                ),
                                width="100%",
                                padding="15px",
                                border_bottom=f"1px solid {TECH_COLORS['gray']}"
                            )
                        )
                    ),
                    width="100%"
                )
            ),
            
            # 添加对话框
            rx.cond(
                WatchlistState.show_add_dialog,
                rx.box(
                    rx.vstack(
                        rx.heading("添加自选股", size="6"),
                        rx.input(
                            placeholder="股票代码 (如 600519.SH)",
                            value=WatchlistState.add_stock_code,
                            on_change=WatchlistState.set_add_stock_code
                        ),
                        rx.input(
                            placeholder="股票名称 (可选)",
                            value=WatchlistState.add_stock_name,
                            on_change=WatchlistState.set_add_stock_name
                        ),
                        rx.hstack(
                            rx.button("取消", on_click=WatchlistState.set_show_add_dialog(False)),
                            rx.button("添加", on_click=WatchlistState.add_to_watchlist),
                            spacing="2"
                        ),
                        spacing="4",
                        padding="20px",
                        bg=TECH_COLORS["dark"],
                        border_radius="12px"
                    ),
                    position="fixed",
                    top="50%",
                    left="50%",
                    transform="translate(-50%, -50%)",
                    z_index="1000"
                )
            ),
            
            spacing="4",
            width="100%",
            max_width="800px",
            margin="0 auto"
        ),
        on_mount=WatchlistState.load_watchlist
    )
```

---

## Task 7: 路由配置

**Files:**
- Modify: `trading_app/trading_app.py`

### Step 1: 添加路由

```python
from watchlist_pages import watchlist_page

# 在路由配置中添加
app.add_page(watchlist_page, route="/watchlist", title="我的自选股", on_load=WatchlistState.load_watchlist)
```

---

## Task 8: 导航更新

**Files:**
- Modify: `trading_app/trading_app.py`

### Step 1: 更新首页添加入口

在首页按钮区域添加：

```python
rx.cond(
    AuthState.is_authenticated,
    rx.link(
        "我的自选股",
        href="/watchlist",
        # ... 样式
    ),
    rx.box()  # 未登录不显示
)
```

---

## 执行顺序

1. Task 1: 数据库设置
2. Task 2: 依赖项安装
3. Task 3: 数据模型实现
4. Task 4: 股票数据API
5. Task 5: 自选股状态管理
6. Task 6: 自选股列表页面
7. Task 7: 路由配置
8. Task 8: 导航更新
