"""
自选股页面 - 分组版
"""
import reflex as rx
from typing import List
from watchlist_state import WatchlistState, TECH_COLORS


def watchlist_page() -> rx.Component:
    return rx.box(
        rx.vstack(
            _header(),
            _index_bar(),
            _title_bar(),
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
                _stock_groups()
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
        on_mount=WatchlistState.on_mount
    )


def _header() -> rx.Component:
    return rx.hstack(
        rx.link("返回", href="/dashboard", color=TECH_COLORS["primary"]),
        rx.spacer(),
        rx.text(WatchlistState.current_user_username, color="#888"),
        rx.button("退出", on_click=WatchlistState.logout, bg="transparent", color=TECH_COLORS["light"]),
        width="100%",
        padding="12px 20px",
        border_bottom=f"1px solid {TECH_COLORS['gray']}"
    )


def _index_bar() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.foreach(WatchlistState.index_quotes, _index_item),
            spacing="3",
            width="100%",
            overflow_x="auto"
        ),
        width="100%",
        padding="12px 0",
        border_bottom=f"1px solid {TECH_COLORS['gray']}"
    )


def _index_item(item: dict) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.text(item["name"], color="#888", font_size="11px"),
            rx.hstack(
                rx.text(item["price"], color=TECH_COLORS["light"], font_weight="bold", font_size="13px"),
                rx.text(
                    item["pct_chg"], 
                    color=rx.cond(item["is_up"], TECH_COLORS["error"], TECH_COLORS["success"]),
                    font_size="11px"
                ),
                spacing="1"
            ),
            spacing="0",
            align_items="start"
        ),
        min_width="80px",
        padding="4px 8px",
        bg=TECH_COLORS["gray"],
        border_radius="6px"
    )


def _title_bar() -> rx.Component:
    return rx.hstack(
        rx.heading("我的自选股", size="7", color=TECH_COLORS["light"]),
        rx.spacer(),
        rx.button("+ 添加", on_click=WatchlistState.open_add_dialog, color_scheme="blue"),
        width="100%",
        padding="16px 0"
    )


def _stock_groups() -> rx.Component:
    return rx.vstack(
        _stock_group("A股", WatchlistState.a_stocks),
        _stock_group("港股", WatchlistState.hk_stocks),
        _stock_group("美股", WatchlistState.us_stocks),
        rx.text(f"最后刷新: {WatchlistState.last_refresh_time}", color="#666", font_size="12px", padding="8px 0"),
        spacing="4",
        width="100%"
    )


def _stock_group(title: str, items: List[dict]) -> rx.Component:
    return rx.cond(
        items.length() > 0,
        rx.vstack(
            rx.text(title, color=TECH_COLORS["primary"], font_weight="bold", font_size="14px", padding_bottom="4px"),
            rx.foreach(items, _stock_item),
            width="100%",
            spacing="2"
        )
    )


def _stock_item(item: dict) -> rx.Component:
    return rx.card(
        rx.hstack(
            rx.vstack(
                rx.text(item["stock_code"], font_weight="bold", color=TECH_COLORS["light"]),
                rx.text(item["stock_name"], color="#888", font_size="12px"),
                spacing="1"
            ),
            rx.spacer(),
            rx.hstack(
                rx.text(item["currency"], color="#888", font_size="12px"),
                rx.text(item["price"], font_weight="bold", color=TECH_COLORS["light"]),
                rx.text(
                    item["pct_chg"], 
                    color=rx.cond(item["is_up"], TECH_COLORS["error"], TECH_COLORS["success"])
                ),
                rx.button(
                    "删除", 
                    on_click=lambda: WatchlistState.remove_from_watchlist(item["id"]), 
                    variant="ghost", 
                    color=TECH_COLORS["error"]
                ),
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
                rx.button("x", on_click=WatchlistState.close_add_dialog, bg="transparent", color=TECH_COLORS["light"]),
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
            rx.divider(),
            rx.cond(
                WatchlistState.selected_stocks.length() > 0,
                rx.vstack(
                    rx.text("已选择:", color=TECH_COLORS["success"], font_weight="bold"),
                    rx.foreach(WatchlistState.selected_stocks, _selected_stock_item),
                    rx.hstack(
                        rx.button("清空", on_click=WatchlistState.clear_selection, variant="outline"),
                        rx.spacer(),
                        rx.button("批量添加", on_click=WatchlistState.add_multiple_to_watchlist, color_scheme="blue"),
                        width="100%"
                    ),
                    width="100%",
                    spacing="2"
                ),
                rx.hstack(
                    rx.button("取消", on_click=WatchlistState.close_add_dialog, variant="outline"),
                    rx.button("添加当前", on_click=WatchlistState.add_to_watchlist, color_scheme="blue"),
                    spacing="2"
                )
            ),
            spacing="3",
            padding="20px",
            bg=TECH_COLORS["darker"],
            border_radius="12px",
            width="380px"
        ),
        position="fixed",
        top="50%",
        left="50%",
        transform="translate(-50%, -50%)",
        bg="rgba(0,0,0,0.95)",
        padding="16px",
        border_radius="12px",
        z_index="1000"
    )


def _search_result_item(item: dict) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.text(item["code"], color=TECH_COLORS["primary"], width="100px", font_weight="bold"),
            rx.text(item["name"], color=TECH_COLORS["light"]),
            width="100%"
        ),
        padding="8px 12px",
        cursor="pointer",
        on_click=lambda: WatchlistState.toggle_stock_selection(item["code"], item["name"]),
        _hover={"bg": "rgba(255,255,255,0.1)"},
        width="100%"
    )


def _selected_stock_item(item: dict) -> rx.Component:
    return rx.hstack(
        rx.text(item["code"], color=TECH_COLORS["primary"], font_size="12px"),
        rx.text(item["name"], color="#888", font_size="12px"),
        rx.button(
            "x",
            on_click=lambda: WatchlistState.toggle_stock_selection(item["code"], item["name"]),
            bg="transparent",
            color=TECH_COLORS["error"],
            size="1",
            padding="0 4px"
        ),
        spacing="2",
        width="100%"
    )
