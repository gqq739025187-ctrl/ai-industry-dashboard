import pandas as pd
import streamlit as st

from dashboard.logic import (
    classify_selloff,
    format_optional_number,
    format_turnover,
    format_volume,
    summarize_status,
)


def render_market_monitor(
    dashboard_data: pd.DataFrame,
    us_dashboard_data: pd.DataFrame,
    a_share_watchlist: pd.DataFrame,
    data_layer,
) -> None:
    if (dashboard_data is None or dashboard_data.empty) and (us_dashboard_data is None or us_dashboard_data.empty):
        st.info("暂无缓存，请点击刷新。")

    st.subheader("A股行情")
    if dashboard_data is None or dashboard_data.empty:
        st.info("A股暂无缓存，请点击刷新。")
    else:
        a_share_display = dashboard_data.copy()
        a_share_display["观察结论"] = a_share_display["change_pct"].apply(classify_selloff)
        a_share_display["状态"] = a_share_display.apply(summarize_status, axis=1)
        a_share_display = a_share_display.rename(
            columns={
                "name": "名称",
                "ticker": "代码",
                "market": "市场",
                "theme": "主题",
                "category": "产业链",
                "latest_price": "最新价",
                "change_pct": "涨跌幅%",
                "turnover": "成交额",
                "ma20": "20日均线",
                "ma60": "60日均线",
            }
        )
        a_share_display["成交额"] = a_share_display["成交额"].apply(format_turnover)
        a_share_display["20日均线"] = a_share_display["20日均线"].apply(format_optional_number)
        a_share_display["60日均线"] = a_share_display["60日均线"].apply(format_optional_number)

        st.dataframe(
            a_share_display[
                ["名称", "代码", "市场", "主题", "产业链", "最新价", "涨跌幅%", "成交额", "20日均线", "60日均线", "观察结论", "状态"]
            ],
            use_container_width=True,
            hide_index=True,
        )

        with st.expander("历史日线数据状态", expanded=False):
            st.dataframe(
                data_layer.local_history_status(a_share_watchlist.to_dict("records")),
                use_container_width=True,
                hide_index=True,
            )
            st.caption("20日/60日均线需要至少 60 条历史日线收盘价。本地文件放在 data/history 文件夹。")

    st.subheader("美股行情")
    if us_dashboard_data is None or us_dashboard_data.empty:
        st.info("美股暂无缓存，请点击刷新。")
        return

    us_display = us_dashboard_data.copy()
    us_display = us_display.rename(
        columns={
            "name": "名称",
            "ticker": "代码",
            "market": "市场",
            "theme": "主题",
            "category": "产业链",
            "latest_price": "最新价",
            "change_pct": "日涨跌幅%",
            "volume": "成交量",
            "status": "状态",
        }
    )
    us_display["最新价"] = us_display["最新价"].apply(format_optional_number)
    us_display["日涨跌幅%"] = us_display["日涨跌幅%"].apply(format_optional_number)
    us_display["成交量"] = us_display["成交量"].apply(format_volume)

    st.dataframe(
        us_display[["名称", "代码", "市场", "主题", "产业链", "最新价", "日涨跌幅%", "成交量", "状态"]],
        use_container_width=True,
        hide_index=True,
    )
