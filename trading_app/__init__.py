import reflex as rx
from pages import (
    register_page,
    login_page,
    password_reset_request_page,
    password_reset_confirm_page
)
from auth import AuthState


class State(AuthState):
    """The app state."""
    pass


def index() -> rx.Component:
    """首页"""
    return rx.center(
        rx.vstack(
            rx.heading("Trading", size="9"),
            rx.text("量化炒股分析平台", size="5"),
            spacing="5",
        ),
        height="100vh",
    )


# Create app instance and add pages.
app = rx.App()

# 添加首页
app.add_page(index, route="/", title="Trading")

# 添加认证页面
app.add_page(register_page, route="/register", title="注册")
app.add_page(login_page, route="/login", title="登录")
app.add_page(password_reset_request_page, route="/reset-password", title="重置密码")
app.add_page(password_reset_confirm_page, route="/reset-password/confirm", title="设置新密码")
