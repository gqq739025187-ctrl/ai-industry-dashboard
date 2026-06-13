from typing import Optional

import pandas as pd


def classify_selloff(change_pct: Optional[float]) -> str:
    if pd.isna(change_pct):
        return "待观察"
    if change_pct <= -5:
        return "可能是情绪杀跌"
    if change_pct <= -2:
        return "轻度回调"
    if change_pct >= 2:
        return "走强"
    return "震荡"


def format_turnover(value) -> str:
    if pd.isna(value):
        return "待获取"
    return f"{float(value) / 100000000:.2f}亿"


def format_optional_number(value) -> str:
    if pd.isna(value):
        return "待获取"
    return f"{float(value):.2f}"


def format_percent(value) -> str:
    if pd.isna(value):
        return "待获取"
    return f"{float(value):.2f}%"


def format_volume(value) -> str:
    if pd.isna(value):
        return "待获取"
    return f"{int(value):,}"


def classify_chain_status(avg_change: Optional[float]) -> str:
    if pd.isna(avg_change):
        return "未刷新行情"
    if avg_change > 1:
        return "强势"
    if avg_change < -1:
        return "弱势"
    return "中性"


def calculate_chain_score(
    avg_change: Optional[float],
    up_ratio: Optional[float],
    above_ma20_ratio: Optional[float],
    above_ma60_ratio: Optional[float],
) -> Optional[int]:
    if pd.isna(avg_change):
        return None

    score = 50
    score += max(min(float(avg_change), 5), -5) * 4
    if up_ratio is not None and pd.notna(up_ratio):
        score += float(up_ratio) * 20
    if above_ma20_ratio is not None and pd.notna(above_ma20_ratio):
        score += float(above_ma20_ratio) * 15
    if above_ma60_ratio is not None and pd.notna(above_ma60_ratio):
        score += float(above_ma60_ratio) * 15
    if float(avg_change) < -2:
        score -= 15

    return int(max(0, min(100, round(score))))


def classify_chain_status_by_score(score: Optional[int]) -> str:
    if score is None or pd.isna(score):
        return "未刷新行情"
    if score >= 70:
        return "强势"
    if score < 45:
        return "弱势"
    return "中性"


def format_ratio_count(count: int, total: int) -> str:
    if total <= 0:
        return "待获取"
    return f"{count}/{total}"


def representative_companies(group: pd.DataFrame, limit: int = 3) -> str:
    names = group["name"].dropna().astype(str).tolist()
    return "、".join(names[:limit])


def combine_text_values(group: pd.DataFrame, column: str, limit: int = 3) -> str:
    if column not in group.columns:
        return ""
    values = []
    for value in group[column].dropna().astype(str):
        if value and value not in values:
            values.append(value)
        if len(values) >= limit:
            break
    return "；".join(values)


def summarize_status(row: pd.Series) -> str:
    if pd.notna(row.get("ma20")) and pd.notna(row.get("ma60")):
        return "正常"

    status = str(row.get("status", ""))
    has_realtime = pd.notna(row.get("latest_price"))
    history_network_failed = (
        "RemoteDisconnected" in status
        or "resolve" in status
        or "nodename" in status
        or "DNS" in status
        or "push2his" in status
    )
    if has_realtime and history_network_failed:
        return "实时成功；日线失败"
    if has_realtime and "AkShare获取失败" in status:
        return "实时成功；均线待获取"
    if has_realtime and "日线" in status:
        return "实时成功；均线待获取"
    if has_realtime:
        return "实时成功"
    if "DNS" in status or "resolve" in status or "nodename" in status:
        return "网络解析失败"
    if status:
        return "获取失败"
    return "待获取"


def build_industry_chain_view(watchlist: pd.DataFrame, *market_frames: pd.DataFrame) -> pd.DataFrame:
    quote_frames = [frame.copy() for frame in market_frames if frame is not None and not frame.empty]
    quote_columns = ["ticker", "latest_price", "change_pct", "turnover", "ma20", "ma60", "status"]
    if quote_frames:
        quotes = pd.concat(quote_frames, ignore_index=True, sort=False)
        quotes = quotes[[column for column in quote_columns if column in quotes.columns]]
        quotes = quotes.drop_duplicates(subset=["ticker"], keep="last")
    else:
        quotes = pd.DataFrame(columns=quote_columns)

    base_columns = [
        "name",
        "ticker",
        "market",
        "theme",
        "category",
        "business",
        "market_focus",
        "description",
    ]
    combined = watchlist[[column for column in base_columns if column in watchlist.columns]].merge(
        quotes,
        on="ticker",
        how="left",
    )
    combined["产业链"] = combined.get("category", pd.Series(dtype="object"))
    if "theme" in combined.columns:
        combined["产业链"] = combined["产业链"].where(combined["产业链"].notna(), combined["theme"])
    combined["产业链"] = combined["产业链"].replace("", pd.NA).fillna("未分类")
    combined["latest_price"] = pd.to_numeric(combined.get("latest_price"), errors="coerce")
    combined["change_pct"] = pd.to_numeric(combined.get("change_pct"), errors="coerce")
    combined["turnover"] = pd.to_numeric(combined.get("turnover"), errors="coerce")
    combined["ma20"] = pd.to_numeric(combined.get("ma20"), errors="coerce")
    combined["ma60"] = pd.to_numeric(combined.get("ma60"), errors="coerce")
    combined["above_ma20"] = combined["latest_price"].notna() & combined["ma20"].notna() & (combined["latest_price"] > combined["ma20"])
    combined["above_ma60"] = combined["latest_price"].notna() & combined["ma60"].notna() & (combined["latest_price"] > combined["ma60"])
    has_market_data = combined["change_pct"].notna().any()

    rows = []
    for chain_name, group in combined.groupby("产业链", dropna=False):
        avg_change = group["change_pct"].dropna().mean()
        total_turnover = group["turnover"].sum(min_count=1)
        member_count = len(group)
        up_count = int((group["change_pct"] > 0).sum())
        down_count = int((group["change_pct"] < 0).sum())
        above_ma20_count = int(group["above_ma20"].sum())
        above_ma60_count = int(group["above_ma60"].sum())
        valid_change_count = int(group["change_pct"].notna().sum())
        valid_ma20_count = int((group["latest_price"].notna() & group["ma20"].notna()).sum())
        valid_ma60_count = int((group["latest_price"].notna() & group["ma60"].notna()).sum())
        up_ratio = up_count / valid_change_count if valid_change_count else None
        above_ma20_ratio = above_ma20_count / valid_ma20_count if valid_ma20_count else None
        above_ma60_ratio = above_ma60_count / valid_ma60_count if valid_ma60_count else None
        score = calculate_chain_score(avg_change, up_ratio, above_ma20_ratio, above_ma60_ratio)
        rows.append(
            {
                "产业链": chain_name,
                "成员数量": member_count,
                "代表公司": representative_companies(group),
                "business": combine_text_values(group, "business"),
                "market_focus": combine_text_values(group, "market_focus"),
                "上涨家数": up_count,
                "下跌家数": down_count,
                "上涨/下跌家数": f"{up_count}/{down_count}" if has_market_data else "未刷新行情",
                "平均涨跌幅%": avg_change,
                "总成交额": total_turnover,
                "20日均线以上数量": above_ma20_count,
                "60日均线以上数量": above_ma60_count,
                "20日均线强度": format_ratio_count(above_ma20_count, valid_ma20_count) if valid_ma20_count else "未刷新",
                "60日均线强度": format_ratio_count(above_ma60_count, valid_ma60_count) if valid_ma60_count else "未刷新",
                "评分": score,
                "状态": classify_chain_status_by_score(score),
            }
        )

    result = pd.DataFrame(rows)
    if has_market_data:
        return result.sort_values(["评分", "平均涨跌幅%"], ascending=[False, False], na_position="last")
    return result.sort_values("产业链")


def build_industry_chain_members(watchlist: pd.DataFrame, chain_name: str, *market_frames: pd.DataFrame) -> pd.DataFrame:
    quote_frames = [frame.copy() for frame in market_frames if frame is not None and not frame.empty]
    quote_columns = ["ticker", "latest_price", "change_pct", "ma20", "ma60", "status"]
    if quote_frames:
        quotes = pd.concat(quote_frames, ignore_index=True, sort=False)
        quotes = quotes[[column for column in quote_columns if column in quotes.columns]]
        quotes = quotes.drop_duplicates(subset=["ticker"], keep="last")
    else:
        quotes = pd.DataFrame(columns=quote_columns)

    base_columns = [
        "name",
        "ticker",
        "market",
        "category",
        "business",
        "market_focus",
        "description",
    ]
    members = watchlist[[column for column in base_columns if column in watchlist.columns]].copy()
    members["产业链"] = members["category"].replace("", pd.NA).fillna("未分类")
    members = members[members["产业链"].eq(chain_name)].merge(quotes, on="ticker", how="left")
    return members


def market_summary_line(label: str, data: pd.DataFrame) -> str:
    if data is None or data.empty or "change_pct" not in data.columns:
        return f"{label}：有效行情不足。"

    valid = data.copy()
    valid["change_pct"] = pd.to_numeric(valid["change_pct"], errors="coerce")
    valid = valid.dropna(subset=["change_pct"])
    if valid.empty:
        return f"{label}：有效行情不足。"

    avg_change = valid["change_pct"].mean()
    up_count = int((valid["change_pct"] > 0).sum())
    down_count = int((valid["change_pct"] < 0).sum())
    strongest = valid.sort_values("change_pct", ascending=False).iloc[0]
    weakest = valid.sort_values("change_pct").iloc[0]
    strongest_name = strongest.get("name", strongest.get("ticker", "未知"))
    weakest_name = weakest.get("name", weakest.get("ticker", "未知"))

    return (
        f"{label}：平均{avg_change:.2f}%，上涨{up_count}家、下跌{down_count}家；"
        f"最强{strongest_name} {strongest['change_pct']:.2f}%，"
        f"最弱{weakest_name} {weakest['change_pct']:.2f}%。"
    )


def industry_summary_line(data: pd.DataFrame) -> str:
    if data is None or data.empty or "平均涨跌幅%" not in data.columns:
        return "产业链：有效分组不足。"

    valid = data.copy()
    valid["平均涨跌幅%"] = pd.to_numeric(valid["平均涨跌幅%"], errors="coerce")
    valid = valid.dropna(subset=["平均涨跌幅%"])
    if valid.empty:
        return "产业链：有效分组不足。"

    best = valid.sort_values("平均涨跌幅%", ascending=False).iloc[0]
    worst = valid.sort_values("平均涨跌幅%").iloc[0]
    weak_count = int(valid["状态"].eq("弱势").sum()) if "状态" in valid.columns else 0
    return (
        f"产业链：最强{best['产业链']} {best['平均涨跌幅%']:.2f}%，"
        f"最弱{worst['产业链']} {worst['平均涨跌幅%']:.2f}%；"
        f"弱势链条{weak_count}个。"
    )


def etf_summary_line(data: pd.DataFrame) -> str:
    if data is None or data.empty or "premium_rate" not in data.columns:
        return "ETF：净值/IOPV不足，暂无法评估溢价。"

    valid = data.copy()
    valid["premium_rate"] = pd.to_numeric(valid["premium_rate"], errors="coerce")
    valid = valid.dropna(subset=["premium_rate"])
    if valid.empty:
        return "ETF：净值/IOPV不足，暂无法评估溢价。"

    highest = valid.sort_values("premium_rate", ascending=False).iloc[0]
    high_premium_count = int((valid["premium_rate"] > 10).sum())
    return (
        f"ETF：最高溢价为{highest['name']} {highest['premium_rate']:.2f}%；"
        f"溢价超过10%的品种{high_premium_count}只。"
    )


def classify_daily_market(
    a_share_data: pd.DataFrame,
    us_data: pd.DataFrame,
    etf_data: pd.DataFrame,
    industry_data: pd.DataFrame,
) -> tuple[str, str]:
    market_frames = []
    for frame in (a_share_data, us_data):
        if frame is not None and not frame.empty and "change_pct" in frame.columns:
            market_frames.append(frame[["change_pct"]].copy())

    if market_frames:
        combined = pd.concat(market_frames, ignore_index=True)
        combined["change_pct"] = pd.to_numeric(combined["change_pct"], errors="coerce")
        combined = combined.dropna(subset=["change_pct"])
    else:
        combined = pd.DataFrame(columns=["change_pct"])

    avg_change = combined["change_pct"].mean() if not combined.empty else None
    down_ratio = float((combined["change_pct"] < 0).mean()) if not combined.empty else 0

    weak_chain_count = 0
    worst_chain_change = None
    if industry_data is not None and not industry_data.empty:
        chain_data = industry_data.copy()
        chain_data["平均涨跌幅%"] = pd.to_numeric(chain_data["平均涨跌幅%"], errors="coerce")
        weak_chain_count = int(chain_data["状态"].eq("弱势").sum()) if "状态" in chain_data.columns else 0
        worst_chain_change = chain_data["平均涨跌幅%"].min()

    high_premium_count = 0
    if etf_data is not None and not etf_data.empty and "premium_rate" in etf_data.columns:
        premium_data = etf_data.copy()
        premium_data["premium_rate"] = pd.to_numeric(premium_data["premium_rate"], errors="coerce")
        high_premium_count = int((premium_data["premium_rate"] > 10).sum())

    if high_premium_count > 0 and avg_change is not None and avg_change <= -1:
        return "估值杀跌", f"市场走弱同时存在{high_premium_count}只ETF溢价超过10%，估值交易拥挤度上升。"

    if weak_chain_count >= 2 or (pd.notna(worst_chain_change) and worst_chain_change <= -3):
        return "逻辑杀跌", f"产业链弱势扩散，弱势链条{weak_chain_count}个，最弱链条跌幅{worst_chain_change:.2f}%。"

    if avg_change is not None and avg_change <= -2 and down_ratio >= 0.7:
        return "情绪杀跌", f"样本平均跌幅{avg_change:.2f}%，下跌占比{down_ratio:.0%}，跌幅呈现普遍扩散。"

    if avg_change is None:
        return "正常波动", "有效行情不足，暂按正常波动处理。"

    return "正常波动", f"样本平均涨跌幅{avg_change:.2f}%，下跌占比{down_ratio:.0%}，未触发异常下跌条件。"


def build_daily_summary(
    a_share_data: pd.DataFrame,
    us_data: pd.DataFrame,
    etf_data: pd.DataFrame,
    industry_data: pd.DataFrame,
) -> str:
    market_type, basis = classify_daily_market(a_share_data, us_data, etf_data, industry_data)
    return "\n\n".join(
        [
            f"市场归因：{market_type}。",
            f"判断依据：{basis}",
            market_summary_line("A股", a_share_data),
            market_summary_line("美股", us_data),
            industry_summary_line(industry_data),
            etf_summary_line(etf_data),
        ]
    )


def combine_market_frames(*frames: pd.DataFrame) -> pd.DataFrame:
    valid_frames = [frame.copy() for frame in frames if frame is not None and not frame.empty]
    if not valid_frames:
        return pd.DataFrame()
    combined = pd.concat(valid_frames, ignore_index=True, sort=False)
    if "change_pct" in combined.columns:
        combined["change_pct"] = pd.to_numeric(combined["change_pct"], errors="coerce")
    return combined


def build_daily_overview(watchlist: pd.DataFrame, industry_data: pd.DataFrame, *market_frames: pd.DataFrame) -> dict:
    market_data = combine_market_frames(*market_frames)
    valid_market = market_data.dropna(subset=["change_pct"]) if "change_pct" in market_data.columns else pd.DataFrame()
    valid_industry = industry_data.dropna(subset=["平均涨跌幅%"]) if "平均涨跌幅%" in industry_data.columns else pd.DataFrame()

    strongest = None
    weakest = None
    if not valid_industry.empty:
        strongest = valid_industry.sort_values("平均涨跌幅%", ascending=False).iloc[0]
        weakest = valid_industry.sort_values("平均涨跌幅%").iloc[0]

    return {
        "股票池公司数量": len(watchlist),
        "产业链数量": watchlist["category"].dropna().astype(str).str.strip().replace("", pd.NA).dropna().nunique(),
        "今日上涨家数": int((valid_market["change_pct"] > 0).sum()) if not valid_market.empty else 0,
        "今日下跌家数": int((valid_market["change_pct"] < 0).sum()) if not valid_market.empty else 0,
        "平均涨跌幅": valid_market["change_pct"].mean() if not valid_market.empty else None,
        "最强产业链": strongest["产业链"] if strongest is not None else "待获取",
        "最弱产业链": weakest["产业链"] if weakest is not None else "待获取",
    }


def classify_market_state(industry_data: pd.DataFrame, etf_data: pd.DataFrame) -> tuple[str, str]:
    valid_industry = industry_data.dropna(subset=["平均涨跌幅%"]) if "平均涨跌幅%" in industry_data.columns else pd.DataFrame()
    high_premium = False
    if etf_data is not None and not etf_data.empty and "premium_rate" in etf_data.columns:
        premium = pd.to_numeric(etf_data["premium_rate"], errors="coerce")
        high_premium = bool((premium >= 10).any())

    if valid_industry.empty:
        base = "请先刷新行情后生成日报"
    else:
        weak_count = int((valid_industry["平均涨跌幅%"] < -1).sum())
        strong_count = int((valid_industry["平均涨跌幅%"] > 1).sum())
        majority = len(valid_industry) / 2
        if weak_count > majority:
            base = "整体偏弱"
        elif strong_count > majority:
            base = "整体偏强"
        else:
            base = "结构分化"

    extra = "部分ETF存在高溢价风险" if high_premium else ""
    return base, extra


def build_daily_conclusion(industry_data: pd.DataFrame, etf_data: pd.DataFrame) -> str:
    market_state, etf_warning = classify_market_state(industry_data, etf_data)
    if market_state == "请先刷新行情后生成日报":
        return market_state

    valid_industry = industry_data.dropna(subset=["平均涨跌幅%"])
    strongest = valid_industry.sort_values("平均涨跌幅%", ascending=False).iloc[0]
    weakest = valid_industry.sort_values("平均涨跌幅%").iloc[0]
    conclusion = f"市场{market_state}，{strongest['产业链']}相对较强，{weakest['产业链']}相对承压。"
    if etf_warning:
        conclusion += f"{etf_warning}，不宜仅凭主题热度判断真实收益。"
    return conclusion


def build_event_focus(events: pd.DataFrame, watchlist: pd.DataFrame, limit: int = 5) -> pd.DataFrame:
    if events is None or events.empty:
        return pd.DataFrame()
    focus = events.copy()
    focus["impact_level"] = pd.to_numeric(focus["impact_level"], errors="coerce").fillna(0)
    focus = focus.sort_values("impact_level", ascending=False).head(limit)
    focus["受影响公司"] = focus["industry"].apply(
        lambda industry: "、".join(watchlist[watchlist["category"].eq(industry)]["name"].astype(str).tolist()) or "暂无映射"
    )
    return focus
