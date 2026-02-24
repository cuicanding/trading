"""
认证页面组件
包含注册、登录、登出和密码重置页面
采用科技感设计风格
"""
import reflex as rx
import secrets
from datetime import datetime, timedelta
from auth import AuthState, require_auth
from models import User, UserRepository, PasswordResetTokenRepository
from email_service import email_service


class RegisterState(AuthState):
    """注册页面状态"""
    
    def handle_register(self):
        """处理注册请求"""
        self.clear_messages()
        self.is_loading = True
        try:
            if self.register_email:
                is_valid, error = self.validate_email(self.register_email)
                if not is_valid:
                    self.error_message = error
                    return
                user_repo = UserRepository()
                if user_repo.email_exists(self.register_email):
                    self.error_message = "该邮箱已被注册"
                    return
            elif self.register_username:
                is_valid, error = self.validate_username(self.register_username)
                if not is_valid:
                    self.error_message = error
                    return
                user_repo = UserRepository()
                if user_repo.username_exists(self.register_username):
                    self.error_message = "该用户名已被注册"
                    return
            else:
                self.error_message = "请输入邮箱或用户名"
                return
            is_valid, error = self.validate_password(self.register_password)
            if not is_valid:
                self.error_message = error
                return
            if self.register_password != self.register_password_confirm:
                self.error_message = "两次输入的密码不一致"
                return
            user_repo = UserRepository()
            user = user_repo.create_user(
                email=self.register_email if self.register_email else None,
                username=self.register_username if self.register_username else None,
                password=self.register_password
            )
            self.login(user)
            if user.email:
                email_service.send_welcome_email(user.email, user.username or user.email)
            self.register_email = ""
            self.register_username = ""
            self.register_password = ""
            self.register_password_confirm = ""
            return rx.redirect("/")
        except Exception as e:
            self.error_message = f"注册失败: {str(e)}"
        finally:
            self.is_loading = False


class LoginState(AuthState):
    """登录页面状态"""
    
    def handle_login(self):
        """处理登录请求"""
        self.clear_messages()
        self.is_loading = True
        try:
            if not self.login_email_or_username:
                self.error_message = "请输入邮箱或用户名"
                return
            if not self.login_password:
                self.error_message = "请输入密码"
                return
            user_repo = UserRepository()
            user = None
            if '@' in self.login_email_or_username:
                user = user_repo.get_user_by_email(self.login_email_or_username)
            else:
                user = user_repo.get_user_by_username(self.login_email_or_username)
            if not user:
                self.error_message = "邮箱或密码错误"
                return
            if not user.verify_password(self.login_password):
                self.error_message = "邮箱或密码错误"
                return
            self.login(user)
            return rx.redirect("/")
        except Exception as e:
            self.error_message = f"登录失败: {str(e)}"
        finally:
            self.is_loading = False


class LogoutState(AuthState):
    """登出页面状态"""
    
    def handle_logout(self):
        """处理登出请求"""
        self.logout()
        # 跳转到登录页面
        return rx.redirect("/login")


class PasswordResetRequestState(AuthState):
    """密码重置请求页面状态"""
    
    reset_email: str = ""
    
    def handle_reset_request(self):
        """处理密码重置请求"""
        self.clear_messages()
        self.is_loading = True
        try:
            is_valid, error = self.validate_email(self.reset_email)
            if not is_valid:
                self.error_message = error
                return
            user_repo = UserRepository()
            user = user_repo.get_user_by_email(self.reset_email)
            if user:
                token = self.generate_secure_token()
                expires_at = self.get_token_expiry(hours=1)
                token_repo = PasswordResetTokenRepository()
                token_repo.create_token(user.id, token, expires_at)
                email_service.send_password_reset_email(user.email, token)
            self.success_message = "如果该邮箱已注册，重置链接将发送到您的邮箱"
            self.reset_email = ""
        except Exception as e:
            self.error_message = f"请求失败: {str(e)}"
        finally:
            self.is_loading = False


class PasswordResetConfirmState(AuthState):
    """密码重置确认页面状态"""
    
    reset_token: str = ""
    new_password: str = ""
    new_password_confirm: str = ""
    
    def on_load(self):
        """页面加载时从URL读取token"""
        token = self.router_data.get("query", {}).get("token", "")
        if token:
            self.reset_token = token[0] if isinstance(token, list) else token
    
    def verify_token(self):
        """验证token是否有效"""
        self.clear_messages()
        
        if not self.reset_token:
            self.error_message = "重置链接无效，请重新请求"
            return False
        
        # 查找token
        token_repo = PasswordResetTokenRepository()
        token_record = token_repo.get_token(self.reset_token)
        
        if not token_record:
            self.error_message = "重置链接无效，请重新请求"
            return False
        
        if token_record.used:
            self.error_message = "重置链接已失效，请重新请求"
            return False
        
        if token_record.is_expired():
            self.error_message = "重置链接已过期，请重新请求"
            return False
        
        return True
    
    def handle_password_reset(self):
        """处理密码重置"""
        self.clear_messages()
        self.is_loading = True
        
        # 验证token
        if not self.verify_token():
            self.is_loading = False
            return
        
        # 验证新密码
        is_valid, error = self.validate_password(self.new_password)
        if not is_valid:
            self.error_message = error
            self.is_loading = False
            return
        
        # 验证确认密码
        if self.new_password != self.new_password_confirm:
            self.error_message = "两次输入的密码不一致"
            self.is_loading = False
            return
        
        # 获取用户ID
        token_repo = PasswordResetTokenRepository()
        token_record = token_repo.get_token(self.reset_token)
        
        # 更新用户密码
        user_repo = UserRepository()
        user = user_repo.get_user_by_id(token_record.user_id)
        
        if user:
            # 更新密码
            new_password_hash = User.hash_password(self.new_password)
            user_repo.conn.execute(
                "UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                [new_password_hash, user.id]
            )
            
            # 标记token为已使用
            token_repo.mark_token_used(self.reset_token)
            
            self.success_message = "密码重置成功，请使用新密码登录"
            self.is_loading = False
            
            # 跳转到登录页面
            return rx.redirect("/login")
        else:
            self.error_message = "用户不存在"
            self.is_loading = False


# 科技感样式配置
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


def tech_card(content: rx.Component) -> rx.Component:
    """科技感卡片容器"""
    return rx.box(
        content,
        bg=TECH_COLORS["dark"],
        border=f"1px solid {TECH_COLORS['primary']}",
        border_radius="16px",
        padding="32px",
        box_shadow=f"0 0 40px rgba(0, 240, 255, 0.1)",
        position="relative",
        overflow="hidden"
    )


def tech_input(placeholder: str, value: str, on_change, input_type: str = "text", width: str = "100%") -> rx.Component:
    """科技感输入框"""
    return rx.input(
        placeholder=placeholder,
        type=input_type,
        value=value,
        on_change=on_change,
        width=width,
        bg=TECH_COLORS["darker"],
        border=f"1px solid {TECH_COLORS['gray']}",
        border_radius="8px",
        padding="16px 20px",
        height="48px",
        color=TECH_COLORS["light"],
        font_size="15px",
        _placeholder={"color": "#666677"},
        _focus={
            "border_color": TECH_COLORS["primary"],
            "box_shadow": f"0 0 20px rgba(0, 240, 255, 0.2)",
            "outline": "none"
        },
        _hover={"border_color": TECH_COLORS["secondary"]}
    )


def tech_button(text: str, on_click, loading: bool, width: str = "100%", color_scheme: str = "blue") -> rx.Component:
    """科技感按钮"""
    return rx.button(
        text,
        on_click=on_click,
        loading=loading,
        width=width,
        bg=f"linear-gradient(135deg, {TECH_COLORS['primary']}, {TECH_COLORS['secondary']})",
        color=TECH_COLORS["dark"],
        border="none",
        border_radius="8px",
        padding="14px 24px",
        font_size="16px",
        font_weight="600",
        cursor="pointer",
        _hover={
            "bg": f"linear-gradient(135deg, {TECH_COLORS['secondary']}, {TECH_COLORS['accent']})",
            "transform": "translateY(-2px)",
            "box_shadow": f"0 8px 30px rgba(0, 240, 255, 0.3)"
        },
        _active={"transform": "translateY(0)"},
        transition="all 0.3s ease"
    )


def tech_link(text: str, href: str) -> rx.Component:
    """科技感链接"""
    return rx.link(
        text,
        href=href,
        color=TECH_COLORS["primary"],
        text_decoration="none",
        font_size="14px",
        _hover={
            "color": TECH_COLORS["accent"],
            "text_decoration": "underline"
        },
        cursor="pointer"
    )


def tech_background() -> rx.Component:
    """科技感背景"""
    return rx.box(
        position="fixed",
        top="0",
        left="0",
        right="0",
        bottom="0",
        bg=TECH_COLORS["darker"],
        z_index="-2"
    )


def tech_heading(text: str, size: str = "8") -> rx.Component:
    """科技感标题"""
    return rx.heading(
        text,
        size=size,
        color=TECH_COLORS["light"],
        font_weight="700",
        text_shadow=f"0 0 20px rgba(0, 240, 255, 0.5)",
        margin_bottom="8px"
    )


def tech_text(text: str, size: str = "4") -> rx.Component:
    """科技感文本"""
    return rx.text(
        text,
        size=size,
        color="#888899",
        margin_bottom="24px"
    )


def register_page() -> rx.Component:
    """注册页面 - 科技感设计"""
    return rx.box(
        tech_background(),
        rx.center(
            tech_card(
                rx.vstack(
                    tech_heading("创建账户", "7"),
                    tech_text("加入AI量化交易平台"),
                    
                    # 邮箱输入
                    rx.vstack(
                        rx.text(
                            "邮箱",
                            font_weight="600",
                            color=TECH_COLORS["light"],
                            font_size="14px",
                            margin_bottom="8px"
                        ),
                        tech_input(
                            placeholder="请输入邮箱",
                            input_type="email",
                            value=RegisterState.register_email,
                            on_change=RegisterState.set_register_email
                        ),
                        align_items="start",
                        width="100%",
                        spacing="0"
                    ),
                    
                    # 分隔线
                    rx.flex(
                        rx.box(flex=1, height="1px", bg=TECH_COLORS["gray"]),
                        rx.text("或", color="#666677", padding="0 16px", font_size="12px"),
                        rx.box(flex=1, height="1px", bg=TECH_COLORS["gray"]),
                        align_items="center",
                        width="100%",
                        margin_y="16px"
                    ),
                    
                    # 用户名输入
                    rx.vstack(
                        rx.text(
                            "用户名",
                            font_weight="600",
                            color=TECH_COLORS["light"],
                            font_size="14px",
                            margin_bottom="8px"
                        ),
                        tech_input(
                            placeholder="请输入用户名",
                            value=RegisterState.register_username,
                            on_change=RegisterState.set_register_username
                        ),
                        align_items="start",
                        width="100%",
                        spacing="0"
                    ),
                    
                    # 密码输入
                    rx.vstack(
                        rx.text(
                            "密码",
                            font_weight="600",
                            color=TECH_COLORS["light"],
                            font_size="14px",
                            margin_bottom="8px"
                        ),
                        tech_input(
                            placeholder="至少8位，包含字母和数字",
                            input_type="password",
                            value=RegisterState.register_password,
                            on_change=RegisterState.set_register_password
                        ),
                        align_items="start",
                        width="100%",
                        spacing="0"
                    ),
                    
                    # 确认密码输入
                    rx.vstack(
                        rx.text(
                            "确认密码",
                            font_weight="600",
                            color=TECH_COLORS["light"],
                            font_size="14px",
                            margin_bottom="8px"
                        ),
                        tech_input(
                            placeholder="请再次输入密码",
                            input_type="password",
                            value=RegisterState.register_password_confirm,
                            on_change=RegisterState.set_register_password_confirm
                        ),
                        align_items="start",
                        width="100%",
                        spacing="0"
                    ),
                    
                    # 错误消息
                    rx.cond(
                        RegisterState.error_message != "",
                        rx.box(
                            rx.text(RegisterState.error_message, color=TECH_COLORS["error"], font_size="14px"),
                            bg="rgba(255, 51, 102, 0.1)",
                            border=f"1px solid {TECH_COLORS['error']}",
                            border_radius="8px",
                            padding="12px",
                            width="100%"
                        )
                    ),
                    
                    # 成功消息
                    rx.cond(
                        RegisterState.success_message != "",
                        rx.box(
                            rx.text(RegisterState.success_message, color=TECH_COLORS["success"], font_size="14px"),
                            bg="rgba(0, 255, 136, 0.1)",
                            border=f"1px solid {TECH_COLORS['success']}",
                            border_radius="8px",
                            padding="12px",
                            width="100%"
                        )
                    ),
                    
                    # 注册按钮
                    tech_button(
                        "立即注册",
                        RegisterState.handle_register,
                        RegisterState.is_loading
                    ),
                    
                    # 登录链接
                    rx.text(
                        "已有账户？",
                        tech_link("立即登录", "/login"),
                        text_align="center",
                        color="#888899",
                        font_size="14px"
                    ),
                    
                    spacing="4",
                    width="420px"
                )
            ),
            height="100vh",
            padding="20px"
        )
    )


def login_page() -> rx.Component:
    """登录页面 - 科技感设计"""
    return rx.box(
        tech_background(),
        rx.center(
            tech_card(
                rx.vstack(
                    tech_heading("欢迎回来", "7"),
                    tech_text("登录AI量化交易平台"),
                    
                    # 邮箱/用户名输入
                    rx.vstack(
                        rx.text(
                            "邮箱或用户名",
                            font_weight="600",
                            color=TECH_COLORS["light"],
                            font_size="14px",
                            margin_bottom="8px"
                        ),
                        tech_input(
                            placeholder="请输入邮箱或用户名",
                            value=LoginState.login_email_or_username,
                            on_change=LoginState.set_login_email_or_username
                        ),
                        align_items="start",
                        width="100%",
                        spacing="0"
                    ),
                    
                    # 密码输入
                    rx.vstack(
                        rx.text(
                            "密码",
                            font_weight="600",
                            color=TECH_COLORS["light"],
                            font_size="14px",
                            margin_bottom="8px"
                        ),
                        tech_input(
                            placeholder="请输入密码",
                            input_type="password",
                            value=LoginState.login_password,
                            on_change=LoginState.set_login_password
                        ),
                        align_items="start",
                        width="100%",
                        spacing="0"
                    ),
                    
                    # 错误消息
                    rx.cond(
                        LoginState.error_message != "",
                        rx.box(
                            rx.text(LoginState.error_message, color=TECH_COLORS["error"], font_size="14px"),
                            bg="rgba(255, 51, 102, 0.1)",
                            border=f"1px solid {TECH_COLORS['error']}",
                            border_radius="8px",
                            padding="12px",
                            width="100%"
                        )
                    ),
                    
                    # 成功消息
                    rx.cond(
                        LoginState.success_message != "",
                        rx.box(
                            rx.text(LoginState.success_message, color=TECH_COLORS["success"], font_size="14px"),
                            bg="rgba(0, 255, 136, 0.1)",
                            border=f"1px solid {TECH_COLORS['success']}",
                            border_radius="8px",
                            padding="12px",
                            width="100%"
                        )
                    ),
                    
                    # 登录按钮
                    tech_button(
                        "登录",
                        LoginState.handle_login,
                        LoginState.is_loading
                    ),
                    
                    # 注册链接
                    rx.text(
                        "还没有账户？",
                        tech_link("立即注册", "/register"),
                        text_align="center",
                        color="#888899",
                        font_size="14px"
                    ),
                    
                    # 忘记密码链接
                    rx.center(
                        tech_link("忘记密码？", "/reset-password"),
                        margin_top="8px"
                    ),
                    
                    spacing="4",
                    width="420px"
                )
            ),
            height="100vh",
            padding="20px"
        )
    )


def password_reset_request_page() -> rx.Component:
    """密码重置请求页面 - 科技感设计"""
    return rx.box(
        tech_background(),
        rx.center(
            tech_card(
                rx.vstack(
                    tech_heading("重置密码", "7"),
                    tech_text("输入您的邮箱以重置密码"),
                    
                    # 邮箱输入
                    rx.vstack(
                        rx.text(
                            "邮箱",
                            font_weight="600",
                            color=TECH_COLORS["light"],
                            font_size="14px",
                            margin_bottom="8px"
                        ),
                        tech_input(
                            placeholder="请输入邮箱",
                            input_type="email",
                            value=PasswordResetRequestState.reset_email,
                            on_change=PasswordResetRequestState.set_reset_email
                        ),
                        align_items="start",
                        width="100%",
                        spacing="0"
                    ),
                    
                    # 错误消息
                    rx.cond(
                        PasswordResetRequestState.error_message != "",
                        rx.box(
                            rx.text(PasswordResetRequestState.error_message, color=TECH_COLORS["error"], font_size="14px"),
                            bg="rgba(255, 51, 102, 0.1)",
                            border=f"1px solid {TECH_COLORS['error']}",
                            border_radius="8px",
                            padding="12px",
                            width="100%"
                        )
                    ),
                    
                    # 成功消息
                    rx.cond(
                        PasswordResetRequestState.success_message != "",
                        rx.box(
                            rx.text(PasswordResetRequestState.success_message, color=TECH_COLORS["success"], font_size="14px"),
                            bg="rgba(0, 255, 136, 0.1)",
                            border=f"1px solid {TECH_COLORS['success']}",
                            border_radius="8px",
                            padding="12px",
                            width="100%"
                        )
                    ),
                    
                    # 发送重置链接按钮
                    tech_button(
                        "发送重置链接",
                        PasswordResetRequestState.handle_reset_request,
                        PasswordResetRequestState.is_loading
                    ),
                    
                    # 返回登录链接
                    rx.center(
                        tech_link("返回登录", "/login"),
                        margin_top="8px"
                    ),
                    
                    spacing="4",
                    width="420px"
                )
            ),
            height="100vh",
            padding="20px"
        )
    )


def password_reset_confirm_page() -> rx.Component:
    """密码重置确认页面 - 科技感设计"""
    return rx.box(
        tech_background(),
        rx.center(
            tech_card(
                rx.vstack(
                    tech_heading("设置新密码", "7"),
                    tech_text("请输入您的新密码"),
                    
                    rx.input(
                        value=PasswordResetConfirmState.reset_token,
                        on_change=PasswordResetConfirmState.set_reset_token,
                        display="none"
                    ),
                    
                    # 新密码输入
                    rx.vstack(
                        rx.text(
                            "新密码",
                            font_weight="600",
                            color=TECH_COLORS["light"],
                            font_size="14px",
                            margin_bottom="8px"
                        ),
                        tech_input(
                            placeholder="至少8位，包含字母和数字",
                            input_type="password",
                            value=PasswordResetConfirmState.new_password,
                            on_change=PasswordResetConfirmState.set_new_password
                        ),
                        align_items="start",
                        width="100%",
                        spacing="0"
                    ),
                    
                    # 确认新密码输入
                    rx.vstack(
                        rx.text(
                            "确认新密码",
                            font_weight="600",
                            color=TECH_COLORS["light"],
                            font_size="14px",
                            margin_bottom="8px"
                        ),
                        tech_input(
                            placeholder="请再次输入新密码",
                            input_type="password",
                            value=PasswordResetConfirmState.new_password_confirm,
                            on_change=PasswordResetConfirmState.set_new_password_confirm
                        ),
                        align_items="start",
                        width="100%",
                        spacing="0"
                    ),
                    
                    # 错误消息
                    rx.cond(
                        PasswordResetConfirmState.error_message != "",
                        rx.box(
                            rx.text(PasswordResetConfirmState.error_message, color=TECH_COLORS["error"], font_size="14px"),
                            bg="rgba(255, 51, 102, 0.1)",
                            border=f"1px solid {TECH_COLORS['error']}",
                            border_radius="8px",
                            padding="12px",
                            width="100%"
                        )
                    ),
                    
                    # 成功消息
                    rx.cond(
                        PasswordResetConfirmState.success_message != "",
                        rx.box(
                            rx.text(PasswordResetConfirmState.success_message, color=TECH_COLORS["success"], font_size="14px"),
                            bg="rgba(0, 255, 136, 0.1)",
                            border=f"1px solid {TECH_COLORS['success']}",
                            border_radius="8px",
                            padding="12px",
                            width="100%"
                        )
                    ),
                    
                    # 重置密码按钮
                    tech_button(
                        "重置密码",
                        PasswordResetConfirmState.handle_password_reset,
                        PasswordResetConfirmState.is_loading
                    ),
                    
                    # 返回登录链接
                    rx.center(
                        tech_link("返回登录", "/login"),
                        margin_top="8px"
                    ),
                    
                    spacing="4",
                    width="420px"
                )
            ),
            height="100vh",
            padding="20px"
        )
    )


