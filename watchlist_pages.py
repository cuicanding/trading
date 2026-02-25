"""
自选股页面 - 简化版
"""
import reflex as rx
from watchlist_state import WatchlistState, TECH_COLORS


def watchlist_page() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.link("← 返回", href="/dashboard", color=TECH_COLORS["primary"]),
                rx.spacer(),
                rx.text(WatchlistState.current_user_username, color="#888"),
                rx.button("退出", on_click=WatchlistState.logout, bg="transparent", color=TECH_COLORS["light"]),
                width="100%",
                padding="12px 20px",
                border_bottom=f"1px solid {TECH_COLORS['gray']}"
            ),
            rx.hstack(
                rx.heading("我的自选股", size="7", color=TECH_COLORS["light"]),
                rx.spacer(),
                rx.hstack(
                    rx.button("刷新", on_click=WatchlistState.refresh_prices, variant="outline"),
                    rx.button("+ 添加", on_click=WatchlistState.open_add_dialog, color_scheme="blue"),
                    spacing="2"
                ),
                width="100%",
                padding="16px 20px"
            ),
            rx.text(f"最后刷新: {WatchlistState.last_refresh_time}", color="#666", font_size="12px", padding="0 20px"),
            rx.cond(
                WatchlistState.error_message != "",
                rx.box(rx.text(WatchlistState.error_message, color="red"), padding="8px")
            ),
            rx.cond(
                WatchlistState.success_message != "",
                rx.box(rx.text(WatchlistState.success_message, color="green"), padding="8px")
            ),
            rx.cond(
                WatchlistState.is_loading,
                rx.spinner(size="3"),
                _stock_list()
            ),
            rx.cond(
                WatchlistState.show_add_dialog,
                _add_dialog()
            ),
            spacing="0",
            width="100%",
            max_width="600px",
            margin="0 auto",
            padding="20px"
        ),
        on_mount=WatchlistState.load_watchlist
    )


def _stock_list() -> rx.Component:
    return rx.cond(
        WatchlistState.watchlist_items.length() > 0,
        rx.foreach(WatchlistState.watchlist_items, _stock_item),
        rx.text("暂无自选股，点击添加按钮", color="#888")
    )


def _stock_item(item: dict) -> rx.Component:
    return rx.card(
        rx.hstack(
            rx.vstack(
                rx.text(item.get("stock_code", ""), font_weight="bold", color=TECH_COLORS["light"]),
                rx.text(item.get("stock_name", ""), color="#888", font_size="12px"),
                spacing="1"
            ),
            rx.spacer(),
            rx.hstack(
                rx.text(item.get("currency", "¥"), color="#888"),
                rx.text(f"{item.get('price', 0):.2f}", font_weight="bold", color=TECH_COLORS["light"]),
                rx.text(f"{item.get('pct_chg', 0):+.2f}%", color=item.get("color", TECH_COLORS["light"])),
                rx.button("删除", on_click=lambda: WatchlistState.remove_from_watchlist(item.get("id", "")), variant="ghost", color=TECH_COLORS["error"]),
                spacing="2"
            ),
            width="100%"
        ),
        width="100%",
        margin_bottom="2"
    )


def _add_dialog() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.heading("添加自选股", size="6"),
                rx.spacer(),
                rx.button("×", on_click=WatchlistState.close_add_dialog, bg="transparent", color=TECH_COLORS["light"]),
                width="100%"
            ),
            rx.input(
                placeholder="股票代码 (如 600519, 09988, AAPL)",
                value=WatchlistState.add_stock_code,
                on_change=WatchlistState.search_with_debounce,
                width="100%"
            ),
            rx.cond(
                WatchlistState.search_results.length() > 0,
                rx.box(
                    rx.foreach(WatchlistState.search_results, _search_result_item),
                    max_height="150px",
                    overflow_y="auto",
                    width="100%",
                    bg=TECH_COLORS["darker"],
                    border_radius="8px",
                    margin_top="4px"
                )
            ),
            rx.hstack(
                rx.text("已选: ", color="#888"),
                rx.text(WatchlistState.add_stock_code, color=TECH_COLORS["primary"]),
                rx.text(WatchlistState.add_stock_name, color=TECH_COLORS["light"])
            ),
            rx.cond(
                WatchlistState.selected_stocks.length() > 0,
                rx.hstack(
                    rx.text(f"已选 {WatchlistState.selected_stocks.length()} 只", color=TECH_COLORS["success"]),
                    rx.spacer(),
                    rx.button("清空", on_click=WatchlistState.clear_selection, variant="outline", size="1"),
                    rx.button("批量添加", on_click=WatchlistState.add_multiple_to_watchlist, color_scheme="blue", size="1"),
                    spacing="2",
                    width="100%"
                ),
                rx.hstack(
                    rx.button("取消", on_click=WatchlistState.close_add_dialog, variant="outline"),
                    rx.button("添加", on_click=WatchlistState.add_to_watchlist, color_scheme="blue"),
                    spacing="2"
                )
            ),
            spacing="4",
            padding="24px",
            bg=TECH_COLORS["darker"],
            border_radius="16px",
            width="400px"
        ),
        position="fixed",
        top="50%",
        left="50%",
        transform="translate(-50%, -50%)",
        bg="rgba(0,0,0,0.9)",
        padding="20px",
        border_radius="16px",
        z_index="1000"
    )


def _search_result_item(item: dict) -> rx.Component:
    code = item.get("code", "")
    name = item.get("name", "")
    return rx.box(
        rx.hstack(
            rx.text(code, color=TECH_COLORS["primary"], width="100px"),
            rx.text(name, color=TECH_COLORS["light"]),
            rx.spacer(),
            rx.icon("check", color=TECH_COLORS["success"], size=16),
            width="100%"
        ),
        padding="8px 12px",
        cursor="pointer",
        on_click=lambda: WatchlistState.toggle_stock_selection(code, name),
        _hover={"bg": "rgba(255,255,255,0.1)"},
        width="100%"
    )
