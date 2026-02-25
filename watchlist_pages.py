"""
自选股页面 - 分组版
"""
import reflex as rx
from typing import List
from watchlist_state import WatchlistState, TECH_COLORS


def watchlist_page() -> rx.Component:
    return rx.fragment(
        # 自动刷新脚本
        rx.script("""
            (function() {
                // 清除旧的定时器
                if (window.autoRefreshInterval) {
                    clearInterval(window.autoRefreshInterval);
                }
                
                // 等待Reflex加载完成
                function startAutoRefresh() {
                    window.autoRefreshInterval = setInterval(function() {
                        // 通过点击隐藏的刷新按钮来触发刷新
                        var refreshBtn = document.getElementById('auto-refresh-trigger');
                        if (refreshBtn) {
                            refreshBtn.click();
                        }
                    }, 5000);
                }
                
                // 页面加载后启动
                if (document.readyState === 'complete') {
                    startAutoRefresh();
                } else {
                    window.addEventListener('load', startAutoRefresh);
                }
            })();
        """),
        # 隐藏的刷新按钮
        rx.button(
            "",
            id="auto-refresh-trigger",
            on_click=WatchlistState.auto_refresh,
            style={"display": "none"}
        ),
        rx.box(
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
                spacing="2",
                width="100%",
                max_width="1200px",
                margin="0 auto",
                padding="16px"
            ),
            on_mount=WatchlistState.on_mount,
            width="100%",
            min_height="100vh",
            bg=TECH_COLORS["darker"]
        )
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
    """指数行情栏 - 分市场展示"""
    return rx.hstack(
        _a_stock_index_block(),
        _hk_index_block(),
        _us_index_block(),
        spacing="2",
        width="100%",
        padding="8px 20px",
        border_bottom=f"1px solid {TECH_COLORS['gray']}"
    )


def _a_stock_index_block() -> rx.Component:
    """A股指数区块"""
    return rx.hstack(
        rx.text("🇨🇳 A股", color=TECH_COLORS["primary"], font_weight="bold", font_size="12px"),
        rx.foreach(WatchlistState.a_indices, _index_item),
        spacing="1",
        flex_wrap="wrap",
        gap="2px"
    )


def _hk_index_block() -> rx.Component:
    """港股指数区块"""
    return rx.hstack(
        rx.text("🇭🇰 港股", color=TECH_COLORS["primary"], font_weight="bold", font_size="12px"),
        rx.foreach(WatchlistState.hk_indices, _index_item),
        spacing="1",
        flex_wrap="wrap",
        gap="2px"
    )


def _us_index_block() -> rx.Component:
    """美股指数区块"""
    return rx.hstack(
        rx.text("🇺🇸 美股", color=TECH_COLORS["primary"], font_weight="bold", font_size="12px"),
        rx.foreach(WatchlistState.us_indices, _index_item),
        spacing="1",
        flex_wrap="wrap",
        gap="2px"
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
                rx.vstack(
                    rx.box(
                        rx.foreach(WatchlistState.search_results, _search_result_item),
                        max_height="150px",
                        overflow_y="auto",
                        width="100%",
                        bg=TECH_COLORS["darker"],
                        border_radius="8px"
                    ),
                    rx.text("💡 提示：灰色项为搜索不到的股票，无法选择添加", 
                           color=TECH_COLORS["gray"], 
                           font_size="12px",
                           margin_top="4px"),
                    width="100%",
                    spacing="1"
                )
            ),
            rx.cond(
                WatchlistState.add_stock_name != "",
                rx.box(
                    rx.text(f"已选择: {WatchlistState.add_stock_code} - {WatchlistState.add_stock_name}", 
                           color=TECH_COLORS["success"], font_size="14px"),
                    margin_top="8px",
                    padding="4px 8px",
                    bg="rgba(0,255,136,0.1)",
                    border_radius="4px"
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
                    rx.button(
                        "添加当前", 
                        on_click=WatchlistState.add_to_watchlist, 
                        color_scheme="blue",
                        disabled=rx.cond(
                            (WatchlistState.add_stock_code != "") & (WatchlistState.add_stock_name == ""),
                            True,
                            False
                        )
                    ),
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
    has_name = item.get("name", "") != ""
    return rx.box(
        rx.hstack(
            rx.text(item["code"], color=TECH_COLORS["primary"], width="100px", font_weight="bold"),
            rx.text(
                rx.cond(
                    has_name,
                    item.get("name", ""),
                    "未知股票"
                ),
                color=rx.cond(
                    has_name,
                    TECH_COLORS["light"],
                    TECH_COLORS["gray"]
                )
            ),
            rx.cond(
                ~has_name,
                rx.text("（无法选择）", color=TECH_COLORS["gray"], font_size="12px")
            ),
            width="100%"
        ),
        padding="8px 12px",
        cursor=rx.cond(
            has_name,
            "pointer",
            "not-allowed"
        ),
        on_click=lambda: WatchlistState.set_selected_stock(item["code"], item.get("name", "")),
        _hover=rx.cond(
            has_name,
            {"bg": "rgba(255,255,255,0.1)"},
            {}
        ),
        opacity=rx.cond(
            has_name,
            1,
            0.5
        ),
        width="100%"
    )


def _selected_stock_item(item: dict) -> rx.Component:
    return rx.hstack(
        rx.text(item["code"], color=TECH_COLORS["primary"], font_size="12px"),
        rx.text(item["name"], color="#888", font_size="12px"),
        rx.button(
            "✓",
            on_click=lambda: WatchlistState.remove_from_selection(item["code"]),
            variant="ghost",
            color=TECH_COLORS["success"],
            size="1",
            padding="0 4px"
        ),
        spacing="2",
        width="100%"
    )
