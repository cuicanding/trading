"""
仪表板页面
用户登录后的主页，展示功能模块入口
"""
import reflex as rx
from auth import AuthState

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
        position="fixed",
        top="0",
        left="0",
        right="0",
        bottom="0",
        bg=TECH_COLORS["darker"],
        z_index="-2"
    )


def nav_bar() -> rx.Component:
    return rx.hstack(
        rx.hstack(
            rx.text(
                "AI",
                font_size="28px",
                font_weight="900",
                color=TECH_COLORS["primary"],
                text_shadow=f"0 0 20px rgba(0, 240, 255, 0.8)"
            ),
            rx.text(
                "QUANT",
                font_size="20px",
                font_weight="600",
                color=TECH_COLORS["light"],
                margin_left="4px"
            ),
        ),
        rx.spacer(),
        rx.hstack(
            rx.text(
                AuthState.current_user_username,
                color=TECH_COLORS["light"],
                font_size="14px"
            ),
            rx.button(
                "退出",
                on_click=AuthState.logout,
                bg="transparent",
                border=f"1px solid {TECH_COLORS['gray']}",
                color=TECH_COLORS["light"],
                border_radius="6px",
                padding="6px 12px",
                font_size="12px",
                _hover={"border_color": TECH_COLORS["error"], "color": TECH_COLORS["error"]}
            ),
            spacing="3"
        ),
        width="100%",
        padding="16px 24px",
        border_bottom=f"1px solid {TECH_COLORS['gray']}",
        bg=TECH_COLORS["dark"]
    )


def feature_card(title: str, desc: str, icon: str, href: str, status: str = "available") -> rx.Component:
    is_available = status == "available"
    border_color = TECH_COLORS["primary"] if is_available else TECH_COLORS["gray"]
    opacity = "1" if is_available else "0.5"
    
    return rx.link(
        rx.box(
            rx.hstack(
                rx.box(
                    icon,
                    font_size="32px",
                    margin_bottom="8px"
                ),
                rx.vstack(
                    rx.hstack(
                        rx.text(
                            title,
                            font_size="18px",
                            font_weight="600",
                            color=TECH_COLORS["light"]
                        ),
                        rx.cond(
                            ~is_available,
                            rx.box(
                                "即将推出",
                                font_size="10px",
                                padding="2px 6px",
                                bg=TECH_COLORS["gray"],
                                color="#888899",
                                border_radius="4px"
                            )
                        )
                    ),
                    rx.text(
                        desc,
                        font_size="14px",
                        color="#888899"
                    ),
                    spacing="1",
                    align_items="start"
                ),
                spacing="4",
                align_items="start"
            ),
            padding="24px",
            bg=f"rgba(0, 240, 255, 0.02)",
            border=f"1px solid {border_color}",
            border_radius="16px",
            width="100%",
            opacity=opacity,
            _hover={
                "bg": f"rgba(0, 240, 255, 0.05)",
                "transform": "translateY(-2px)",
                "box_shadow": f"0 8px 30px rgba(0, 240, 255, 0.1)"
            } if is_available else {},
            transition="all 0.3s ease"
        ),
        href=href if is_available else "#",
        text_decoration="none"
    )


def dashboard_page() -> rx.Component:
    """仪表板页面"""
    return rx.box(
        tech_background(),
        rx.vstack(
            nav_bar(),
            rx.vstack(
                rx.heading(
                    "欢迎回来",
                    size="8",
                    color=TECH_COLORS["light"],
                    margin_bottom="8px"
                ),
                rx.text(
                    "选择一个功能模块开始",
                    font_size="16px",
                    color="#888899",
                    margin_bottom="32px"
                ),
                rx.grid(
                    feature_card(
                        "自选追踪",
                        "管理您的自选股票，实时追踪行情变化",
                        "⭐",
                        "/watchlist",
                        "available"
                    ),
                    feature_card(
                        "市场研究",
                        "市场热点、板块轮动、资金流向分析",
                        "📊",
                        "/market",
                        "coming"
                    ),
                    feature_card(
                        "智能分析",
                        "AI驱动的股票分析和预测",
                        "🤖",
                        "/analysis",
                        "coming"
                    ),
                    feature_card(
                        "策略回测",
                        "量化策略回测和优化",
                        "🎯",
                        "/backtest",
                        "coming"
                    ),
                    feature_card(
                        "风险监控",
                        "持仓风险分析和预警",
                        "⚠️",
                        "/risk",
                        "coming"
                    ),
                    feature_card(
                        "数据报表",
                        "投资收益统计和报告",
                        "📈",
                        "/reports",
                        "coming"
                    ),
                    columns="2",
                    spacing="4",
                    width="100%"
                ),
                spacing="0",
                width="100%",
                max_width="900px",
                padding="32px 24px"
            ),
            spacing="0",
            width="100%",
            min_height="100vh"
        ),
        on_mount=AuthState.check_auth
    )
