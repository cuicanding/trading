"""
数据模型
定义User和PasswordResetToken数据模型
"""
import duckdb
import uuid
import bcrypt
from datetime import datetime
from typing import Optional, List


class User:
    """用户数据模型"""
    
    def __init__(
        self,
        id: str,
        email: Optional[str] = None,
        username: Optional[str] = None,
        password_hash: str = "",
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self.id = id
        self.email = email
        self.username = username
        self.password_hash = password_hash
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
    
    @staticmethod
    def hash_password(password: str) -> str:
        """使用bcrypt加密密码"""
        salt = bcrypt.gensalt(rounds=10)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def verify_password(self, password: str) -> bool:
        """验证密码是否正确"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'password_hash': self.password_hash,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class PasswordResetToken:
    """密码重置Token数据模型"""
    
    def __init__(
        self,
        id: str,
        user_id: str,
        token: str,
        expires_at: datetime,
        used: bool = False,
        created_at: Optional[datetime] = None
    ):
        self.id = id
        self.user_id = user_id
        self.token = token
        self.expires_at = expires_at
        self.used = used
        self.created_at = created_at or datetime.now()
    
    def is_expired(self) -> bool:
        """检查token是否过期"""
        return datetime.now() > self.expires_at
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'token': self.token,
            'expires_at': self.expires_at.isoformat(),
            'used': self.used,
            'created_at': self.created_at.isoformat()
        }


class UserRepository:
    """用户数据访问层"""
    
    def __init__(self, db_path: str = "trading.db"):
        self.db_path = db_path
        self.conn = None
    
    def connect(self):
        """连接到数据库"""
        if self.conn is None:
            self.conn = duckdb.connect(self.db_path)
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def create_user(self, email: Optional[str] = None, username: Optional[str] = None, password: str = "") -> User:
        """创建新用户"""
        self.connect()
        
        # 生成UUID
        user_id = str(uuid.uuid4())
        
        # 加密密码
        password_hash = User.hash_password(password)
        
        # 插入用户记录
        self.conn.execute(
            "INSERT INTO users (id, email, username, password_hash) VALUES (?, ?, ?, ?)",
            [user_id, email, username, password_hash]
        )
        
        # 创建User对象
        user = User(
            id=user_id,
            email=email,
            username=username,
            password_hash=password_hash
        )
        
        return user
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """通过邮箱获取用户"""
        self.connect()
        
        result = self.conn.execute(
            "SELECT * FROM users WHERE email = ?",
            [email]
        ).fetchone()
        
        if result:
            return User(
                id=str(result[0]),
                email=result[1],
                username=result[2],
                password_hash=result[3],
                created_at=result[4],
                updated_at=result[5]
            )
        
        return None
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """通过用户名获取用户"""
        self.connect()
        
        result = self.conn.execute(
            "SELECT * FROM users WHERE username = ?",
            [username]
        ).fetchone()
        
        if result:
            return User(
                id=str(result[0]),
                email=result[1],
                username=result[2],
                password_hash=result[3],
                created_at=result[4],
                updated_at=result[5]
            )
        
        return None
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """通过ID获取用户"""
        self.connect()
        
        result = self.conn.execute(
            "SELECT * FROM users WHERE id = ?",
            [user_id]
        ).fetchone()
        
        if result:
            return User(
                id=str(result[0]),
                email=result[1],
                username=result[2],
                password_hash=result[3],
                created_at=result[4],
                updated_at=result[5]
            )
        
        return None
    
    def email_exists(self, email: str) -> bool:
        """检查邮箱是否存在"""
        self.connect()
        
        result = self.conn.execute(
            "SELECT COUNT(*) FROM users WHERE email = ?",
            [email]
        ).fetchone()
        
        return result[0] > 0
    
    def username_exists(self, username: str) -> bool:
        """检查用户名是否存在"""
        self.connect()
        
        result = self.conn.execute(
            "SELECT COUNT(*) FROM users WHERE username = ?",
            [username]
        ).fetchone()
        
        return result[0] > 0


class PasswordResetTokenRepository:
    """密码重置Token数据访问层"""
    
    def __init__(self, db_path: str = "trading.db"):
        self.db_path = db_path
        self.conn = None
    
    def connect(self):
        """连接到数据库"""
        if self.conn is None:
            self.conn = duckdb.connect(self.db_path)
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def create_token(self, user_id: str, token: str, expires_at: datetime) -> PasswordResetToken:
        """创建密码重置token"""
        self.connect()
        
        # 生成UUID
        token_id = str(uuid.uuid4())
        
        # 插入token记录
        self.conn.execute(
            "INSERT INTO password_reset_tokens (id, user_id, token, expires_at) VALUES (?, ?, ?, ?)",
            [token_id, user_id, token, expires_at.isoformat()]
        )
        
        # 创建PasswordResetToken对象
        reset_token = PasswordResetToken(
            id=token_id,
            user_id=user_id,
            token=token,
            expires_at=expires_at
        )
        
        return reset_token
    
    def get_token(self, token: str) -> Optional[PasswordResetToken]:
        """通过token获取记录"""
        self.connect()
        
        result = self.conn.execute(
            "SELECT * FROM password_reset_tokens WHERE token = ?",
            [token]
        ).fetchone()
        
        if result:
            expires_at = result[3]
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at)
            return PasswordResetToken(
                id=result[0],
                user_id=result[1],
                token=result[2],
                expires_at=expires_at,
                used=result[4],
                created_at=result[5]
            )
        
        return None
    
    def mark_token_used(self, token: str):
        """标记token为已使用"""
        self.connect()
        
        self.conn.execute(
            "UPDATE password_reset_tokens SET used = TRUE WHERE token = ?",
            [token]
        )


class WatchlistGroup:
    """自选股分组"""
    
    def __init__(self, id: str, user_id: str, name: str, sort_order: int = 0, created_at: Optional[datetime] = None):
        self.id = id
        self.user_id = user_id
        self.name = name
        self.sort_order = sort_order
        self.created_at = created_at or datetime.now()
    
    def to_dict(self) -> dict:
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'name': self.name,
            'sort_order': self.sort_order,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class WatchlistItem:
    """自选股项目"""
    
    def __init__(self, id: str, user_id: str, stock_code: str, stock_name: str = "", group_id: Optional[str] = None, sort_order: int = 0, created_at: Optional[datetime] = None):
        self.id = id
        self.user_id = user_id
        self.stock_code = stock_code
        self.stock_name = stock_name
        self.group_id = group_id
        self.sort_order = sort_order
        self.created_at = created_at or datetime.now()
    
    def to_dict(self) -> dict:
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'stock_code': self.stock_code,
            'stock_name': self.stock_name,
            'group_id': str(self.group_id) if self.group_id else None,
            'sort_order': self.sort_order,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class WatchlistGroupRepository:
    """自选股分组数据访问层"""
    
    def __init__(self, db_path: str = "trading.db"):
        self.db_path = db_path
        self.conn = None
    
    def connect(self):
        if self.conn is None:
            self.conn = duckdb.connect(self.db_path)
    
    def create_group(self, user_id: str, name: str) -> WatchlistGroup:
        self.connect()
        group_id = str(uuid.uuid4())
        self.conn.execute(
            "INSERT INTO watchlist_groups (id, user_id, name) VALUES (?, ?, ?)",
            [group_id, user_id, name]
        )
        return WatchlistGroup(id=group_id, user_id=user_id, name=name)
    
    def get_groups_by_user(self, user_id: str) -> list:
        self.connect()
        result = self.conn.execute(
            "SELECT * FROM watchlist_groups WHERE user_id = ? ORDER BY sort_order, created_at",
            [user_id]
        ).fetchall()
        return [
            WatchlistGroup(
                id=str(row[0]),
                user_id=str(row[1]),
                name=row[2],
                sort_order=row[3],
                created_at=row[4]
            )
            for row in result
        ]
    
    def delete_group(self, group_id: str):
        self.connect()
        self.conn.execute("DELETE FROM watchlist_items WHERE group_id = ?", [group_id])
        self.conn.execute("DELETE FROM watchlist_groups WHERE id = ?", [group_id])


class WatchlistItemRepository:
    """自选股项目数据访问层"""
    
    def __init__(self, db_path: str = "trading.db"):
        self.db_path = db_path
        self.conn = None
    
    def connect(self):
        if self.conn is None:
            self.conn = duckdb.connect(self.db_path)
    
    def add_item(self, user_id: str, stock_code: str, stock_name: str = "", group_id: str = None) -> WatchlistItem:
        self.connect()
        item_id = str(uuid.uuid4())
        self.conn.execute(
            "INSERT INTO watchlist_items (id, user_id, stock_code, stock_name, group_id) VALUES (?, ?, ?, ?, ?)",
            [item_id, user_id, stock_code, stock_name, group_id]
        )
        return WatchlistItem(id=item_id, user_id=user_id, stock_code=stock_code, stock_name=stock_name, group_id=group_id)
    
    def get_items_by_user(self, user_id: str, group_id: str = None) -> list:
        self.connect()
        if group_id:
            result = self.conn.execute(
                "SELECT * FROM watchlist_items WHERE user_id = ? AND group_id = ? ORDER BY sort_order, created_at DESC",
                [user_id, group_id]
            ).fetchall()
        else:
            result = self.conn.execute(
                "SELECT * FROM watchlist_items WHERE user_id = ? ORDER BY sort_order, created_at DESC",
                [user_id]
            ).fetchall()
        return [
            WatchlistItem(
                id=str(row[0]),
                user_id=str(row[1]),
                stock_code=row[2],
                stock_name=row[3],
                group_id=str(row[4]) if row[4] else None,
                sort_order=row[5],
                created_at=row[6]
            )
            for row in result
        ]
    
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
