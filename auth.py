"""
认证状态管理
实现AuthState和认证相关的逻辑
"""
import reflex as rx
import secrets
from datetime import datetime, timedelta
from typing import Optional
from models import User, UserRepository


class AuthState(rx.State):
    """认证状态基类"""
    
    current_user_id: Optional[str] = None
    current_user_email: Optional[str] = None
    current_user_username: Optional[str] = None
    
    register_email: str = ""
    register_username: str = ""
    register_password: str = ""
    register_password_confirm: str = ""
    
    login_email_or_username: str = ""
    login_password: str = ""
    
    error_message: str = ""
    success_message: str = ""
    
    is_loading: bool = False
    
    @property
    def is_authenticated(self) -> bool:
        """检查用户是否已认证"""
        return self.current_user_id is not None
    
    @property
    def current_user(self) -> Optional[dict]:
        """获取当前用户信息"""
        if self.current_user_id:
            return {
                "id": self.current_user_id,
                "email": self.current_user_email,
                "username": self.current_user_username
            }
        return None
    
    def login(self, user: User):
        """登录用户"""
        self.current_user_id = user.id
        self.current_user_email = user.email
        self.current_user_username = user.username
        self.success_message = "登录成功"
        self.error_message = ""
    
    def logout(self):
        """登出用户"""
        self.current_user_id = None
        self.current_user_email = None
        self.current_user_username = None
        self.success_message = "登出成功"
        self.error_message = ""
    
    def clear_messages(self):
        """清除消息"""
        self.error_message = ""
        self.success_message = ""
    
    def validate_email(self, email: str) -> tuple[bool, str]:
        """验证邮箱格式"""
        if not email:
            return False, "邮箱不能为空"
        if '@' not in email or '.' not in email:
            return False, "邮箱格式无效"
        return True, ""
    
    def validate_username(self, username: str) -> tuple[bool, str]:
        """验证用户名格式"""
        if not username:
            return False, "用户名不能为空"
        if len(username) < 3 or len(username) > 20:
            return False, "用户名长度必须在3-20个字符之间"
        if not username.replace('_', '').isalnum():
            return False, "用户名只能包含字母、数字和下划线"
        return True, ""
    
    def validate_password(self, password: str) -> tuple[bool, str]:
        """验证密码强度"""
        if not password:
            return False, "密码不能为空"
        if len(password) < 8:
            return False, "密码长度至少需要8位"
        has_letter = any(c.isalpha() for c in password)
        has_digit = any(c.isdigit() for c in password)
        if not (has_letter and has_digit):
            return False, "密码必须包含字母和数字"
        return True, ""
    
    def generate_secure_token(self) -> str:
        """生成安全的token"""
        return secrets.token_urlsafe(32)
    
    def get_token_expiry(self, hours: int = 1) -> datetime:
        """获取token过期时间"""
        return datetime.now() + timedelta(hours=hours)


def require_auth(page_func):
    """认证装饰器，保护需要认证的页面"""
    def wrapper(self):
        if not self.is_authenticated:
            return rx.redirect("/login")
        return page_func(self)
    return wrapper
