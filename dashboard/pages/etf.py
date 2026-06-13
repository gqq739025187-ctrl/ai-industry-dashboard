import pandas as pd
import streamlit as st

from dashboard.logic import format_optional_number, format_percent


def render_etf_monitor(etf_premium_data: pd.DataFrame) -> None:
    st.subheader("ETF溢价监控")
    if etf_premium_data is None or etf_premium_data.empty:
        st.info("暂无缓存，请点击刷新。")
        return

    warning_rows = etf_premium_data[etf_premium_data["premium_rate"] > 10]
    if not warning_rows.empty:
        warning_names = "、".join(warning_rows["name"].astype(str).tolist())
        st.error(f"{warning_names} 溢价率超过10%，注意溢价风险。")

    display = etf_premium_data.rename(
        columns={
            "name": "名称",
            "ticker": "代码",
            "latest_price": "市场价格",
            "iopv": "IOPV",
            "nav": "净值",
            "valuation_source": "估值来源",
            "premium_rate": "溢价率",
            "risk": "风险等级",
            "status": "状态",
        }
    )
    display["市场价格"] = display["市场价格"].apply(format_optional_number)
    display["IOPV"] = display["IOPV"].apply(format_optional_number)
    display["净值"] = display["净值"].apply(format_optional_number)
    display["溢价率"] = display["溢价率"].apply(format_percent)

    st.dataframe(
        display[["名称", "代码", "市场价格", "IOPV", "净值", "估值来源", "溢价率", "风险等级", "状态"]],
        use_container_width=True,
        hide_index=True,
    )
