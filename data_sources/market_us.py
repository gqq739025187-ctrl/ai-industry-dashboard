from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from typing import List

import pandas as pd

from .utils import timed_log


@timed_log
def fetch_us_market_data(watchlist_records: List[dict]) -> pd.DataFrame:
    print("[外部接口] 美股批量行情 开始")
    rows = []
    us_records = [record for record in watchlist_records if record["market"] == "美股"]

    try:
        import yfinance as yf
    except Exception as error:
        return pd.DataFrame(
            [
                {
                    "ticker": record["ticker"],
                    "latest_price": None,
                    "change_pct": None,
                    "volume": None,
                    "turnover": None,
                    "status": f"yfinance未安装或无法导入: {error}",
                }
                for record in us_records
            ]
        )

    tickers = [record["ticker"] for record in us_records]
    batch_history = None
    batch_error = None
    try:
        yfinance_output = StringIO()
        with redirect_stdout(yfinance_output), redirect_stderr(yfinance_output):
            batch_history = yf.download(
                tickers,
                period="5d",
                interval="1d",
                progress=False,
                threads=True,
                group_by="column",
                auto_adjust=False,
                timeout=10,
            )
        if batch_history.empty:
            detail = yfinance_output.getvalue().strip()
            raise ValueError(f"yfinance批量返回空数据；{detail}" if detail else "yfinance批量返回空数据")
    except Exception as error:
        batch_error = error
        batch_history = None

    if batch_history is None:
        return pd.DataFrame(
            [
                {
                    "ticker": record["ticker"],
                    "latest_price": None,
                    "change_pct": None,
                    "volume": None,
                    "turnover": None,
                    "status": f"yfinance批量获取失败，未逐只降级以避免长时间等待: {batch_error}",
                }
                for record in us_records
            ]
        )

    for record in us_records:
        ticker = record["ticker"]
        try:
            rows.append(parse_yfinance_history(ticker, extract_yfinance_ticker_history(batch_history, ticker), "正常"))
        except Exception as batch_parse_error:
            rows.append(fetch_single_us_market_data(yf, ticker, batch_parse_error))

    return pd.DataFrame(rows)


def extract_yfinance_ticker_history(history: pd.DataFrame, ticker: str) -> pd.DataFrame:
    if not isinstance(history.columns, pd.MultiIndex):
        return history
    if ticker in history.columns.get_level_values(-1):
        return history.xs(ticker, level=-1, axis=1)
    if ticker in history.columns.get_level_values(0):
        return history.xs(ticker, level=0, axis=1)
    raise ValueError(f"批量结果中没有 {ticker}")


def parse_yfinance_history(ticker: str, history: pd.DataFrame, success_status: str) -> dict:
    if history.empty:
        raise ValueError("yfinance返回空数据")

    latest_row = history.dropna(subset=["Close"]).iloc[-1]
    previous_rows = history.dropna(subset=["Close"]).iloc[:-1]
    if previous_rows.empty:
        raise ValueError("yfinance返回数据不足，无法计算日涨跌幅")

    previous_close = previous_rows.iloc[-1]["Close"]
    latest_price = latest_row["Close"]
    if pd.isna(previous_close) or float(previous_close) == 0:
        raise ValueError("前收盘价为空或为0，无法计算日涨跌幅")

    volume = int(latest_row["Volume"]) if pd.notna(latest_row["Volume"]) else None
    return {
        "ticker": ticker,
        "latest_price": float(latest_price),
        "change_pct": (float(latest_price) / float(previous_close) - 1) * 100,
        "volume": volume,
        "turnover": float(latest_price) * float(volume) if volume is not None else None,
        "status": success_status,
    }


@timed_log
def fetch_single_us_market_data(yf, ticker: str, batch_error: Exception) -> dict:
    print(f"[外部接口] 美股单票降级 {ticker} 开始")
    try:
        yfinance_output = StringIO()
        with redirect_stdout(yfinance_output), redirect_stderr(yfinance_output):
            history = yf.download(
                ticker,
                period="5d",
                interval="1d",
                progress=False,
                threads=False,
                auto_adjust=False,
                timeout=3,
            )
        if history.empty:
            detail = yfinance_output.getvalue().strip()
            raise ValueError(f"yfinance返回空数据；{detail}" if detail else "yfinance返回空数据")
        if isinstance(history.columns, pd.MultiIndex):
            history = extract_yfinance_ticker_history(history, ticker)
        return parse_yfinance_history(ticker, history, f"正常；批量降级原因: {batch_error}")
    except Exception as error:
        return {
            "ticker": ticker,
            "latest_price": None,
            "change_pct": None,
            "volume": None,
            "turnover": None,
            "status": f"yfinance获取失败: {error}; 批量失败原因: {batch_error}",
        }
