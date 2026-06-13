#!/bin/zsh
set -e

cd "$(dirname "$0")"

echo "Updating local A-share history with AkShare..."
echo

mkdir -p data/history

.venv/bin/python - <<'PY'
from datetime import datetime
from pathlib import Path

import akshare as ak

targets = [
    ("新易盛", "300502.SZ", "300502"),
    ("中际旭创", "300308.SZ", "300308"),
    ("天孚通信", "300394.SZ", "300394"),
    ("光迅科技", "002281.SZ", "002281"),
]

out_dir = Path("data/history")
end_date = datetime.now().strftime("%Y%m%d")

for name, ticker, symbol in targets:
    print(f"Fetching {name} {ticker}...")
    df = ak.stock_zh_a_hist(
        symbol=symbol,
        period="daily",
        start_date="20200101",
        end_date=end_date,
        adjust="qfq",
    )
    if df.empty:
        raise RuntimeError(f"{ticker} returned empty data")

    df = df.rename(
        columns={
            "日期": "date",
            "收盘": "close",
            "成交额": "amount",
            "涨跌幅": "change_pct",
        }
    )
    df[["date", "close", "amount", "change_pct"]].to_csv(
        out_dir / f"{ticker}.csv",
        index=False,
    )
    print(f"Saved {ticker}: {len(df)} rows")

print()
print("History update completed.")
PY

echo
echo "Done. Refresh http://localhost:8502 after restarting Streamlit if needed."
echo "Press Enter to close this window."
read
