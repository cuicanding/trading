import reflex as rx
from pages import (
    register_page,
    login_page,
    password_reset_request_page,
    password_reset_confirm_page,
    PasswordResetConfirmState
)
from auth import AuthState


class State(AuthState):
    """The app state."""
    pass


# 科技感颜色配置
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


def tech_button(text: str, href: str, variant: str = "primary") -> rx.Component:
    """科技感按钮"""
    if variant == "primary":
        return rx.link(
            text,
            href=href,
            bg=f"linear-gradient(135deg, {TECH_COLORS['primary']}, {TECH_COLORS['secondary']})",
            color=TECH_COLORS["dark"],
            padding="16px 32px",
            border_radius="12px",
            font_size="16px",
            font_weight="600",
            text_decoration="none",
            _hover={
                "bg": f"linear-gradient(135deg, {TECH_COLORS['secondary']}, {TECH_COLORS['accent']})",
                "transform": "translateY(-2px)",
                "box_shadow": f"0 8px 30px rgba(0, 240, 255, 0.3)"
            },
            _active={"transform": "translateY(0)"},
            transition="all 0.3s ease"
        )
    else:
        return rx.link(
            text,
            href=href,
            bg="transparent",
            border=f"2px solid {TECH_COLORS['primary']}",
            color=TECH_COLORS["primary"],
            padding="16px 32px",
            border_radius="12px",
            font_size="16px",
            font_weight="600",
            text_decoration="none",
            _hover={
                "bg": f"rgba(0, 240, 255, 0.1)",
                "border_color": TECH_COLORS["accent"],
                "color": TECH_COLORS["accent"]
            },
            transition="all 0.3s ease"
        )


def index() -> rx.Component:
    """首页 - 科技感设计"""
    return rx.box(
        tech_background(),
        rx.center(
            rx.vstack(
                # Logo区域
                rx.box(
                    rx.text(
                        "AI",
                        font_size="80px",
                        font_weight="900",
                        color=TECH_COLORS["primary"],
                        text_shadow=f"0 0 40px rgba(0, 240, 255, 0.8)",
                        letter_spacing="8px"
                    ),
                    margin_bottom="16px"
                ),
                
                # 主标题
                rx.heading(
                    "QUANT TRADING",
                    size="9",
                    color=TECH_COLORS["light"],
                    font_weight="800",
                    letter_spacing="4px",
                    text_shadow=f"0 0 30px rgba(0, 240, 255, 0.5)",
                    margin_bottom="8px"
                ),
                
                # 副标题
                rx.text(
                    "智能量化 · 数据驱动 · 精准决策",
                    font_size="20px",
                    color="#888899",
                    letter_spacing="2px",
                    margin_bottom="48px"
                ),
                
                # 功能特性
                rx.hstack(
                    # 特性1
                    rx.box(
                        rx.box(
                            "🤖",
                            font_size="32px",
                            margin_bottom="12px"
                        ),
                        rx.text(
                            "AI驱动",
                            font_size="16px",
                            font_weight="600",
                            color=TECH_COLORS["light"],
                            margin_bottom="4px"
                        ),
                        rx.text(
                            "智能算法分析",
                            font_size="12px",
                            color="#666677"
                        ),
                        bg="rgba(0, 240, 255, 0.05)",
                        border=f"1px solid {TECH_COLORS['primary']}",
                        border_radius="12px",
                        padding="20px",
                        width="160px",
                        text_align="center"
                    ),
                    
                    # 特性2
                    rx.box(
                        rx.box(
                            "📊",
                            font_size="32px",
                            margin_bottom="12px"
                        ),
                        rx.text(
                            "实时数据",
                            font_size="16px",
                            font_weight="600",
                            color=TECH_COLORS["light"],
                            margin_bottom="4px"
                        ),
                        rx.text(
                            "毫秒级更新",
                            font_size="12px",
                            color="#666677"
                        ),
                        bg="rgba(112, 0, 255, 0.05)",
                        border=f"1px solid {TECH_COLORS['secondary']}",
                        border_radius="12px",
                        padding="20px",
                        width="160px",
                        text_align="center"
                    ),
                    
                    # 特性3
                    rx.box(
                        rx.box(
                            "🎯",
                            font_size="32px",
                            margin_bottom="12px"
                        ),
                        rx.text(
                            "精准预测",
                            font_size="16px",
                            font_weight="600",
                            color=TECH_COLORS["light"],
                            margin_bottom="4px"
                        ),
                        rx.text(
                            "高胜率策略",
                            font_size="12px",
                            color="#666677"
                        ),
                        bg="rgba(255, 0, 170, 0.05)",
                        border=f"1px solid {TECH_COLORS['accent']}",
                        border_radius="12px",
                        padding="20px",
                        width="160px",
                        text_align="center"
                    ),
                    
                    spacing="4",
                    margin_bottom="48px"
                ),
                
                # 按钮区域
                rx.hstack(
                    tech_button("立即注册", "/register", "primary"),
                    tech_button("立即登录", "/login", "secondary"),
                    spacing="4"
                ),
                
                # 底部链接
                rx.hstack(
                    rx.link(
                        "忘记密码？",
                        href="/reset-password",
                        color="#666677",
                        font_size="14px",
                        text_decoration="none",
                        _hover={"color": TECH_COLORS["primary"]}
                    ),
                    rx.box(width="1px", height="16px", bg="#2a2a35", margin_x="16px"),
                    rx.text(
                        "© 2025 AI Quant Trading",
                        color="#666677",
                        font_size="14px"
                    ),
                    spacing="2",
                    margin_top="32px"
                ),
                
                spacing="4",
                text_align="center"
            ),
            height="100vh",
            padding="20px"
        )
    )


# Create app instance and add pages.
app = rx.App()

# 添加首页
app.add_page(index, route="/", title="AI Quant Trading")

# 添加认证页面
app.add_page(register_page, route="/register", title="注册")
app.add_page(login_page, route="/login", title="登录")
app.add_page(password_reset_request_page, route="/reset-password", title="重置密码")
app.add_page(password_reset_confirm_page, route="/reset-password/confirm", title="设置新密码", on_load=PasswordResetConfirmState.on_load)
