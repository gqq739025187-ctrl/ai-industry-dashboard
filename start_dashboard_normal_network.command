#!/bin/zsh
set -e

cd "$(dirname "$0")"

PORT=8503

echo "Starting AI investment dashboard from normal Terminal..."
echo
echo "This window uses your Mac's normal network path, not the Codex sandbox."
echo "Dashboard URL: http://localhost:${PORT}"
echo

echo "Checking network from this Terminal..."
.venv/bin/python - <<'PY'
import socket

for host in ["www.baidu.com", "push2his.eastmoney.com", "qt.gtimg.cn"]:
    try:
        ip = socket.gethostbyname(host)
        print(f"OK   {host} -> {ip}")
    except Exception as error:
        print(f"FAIL {host} -> {error}")
PY

echo
echo "Looking for a local proxy..."
PROXY_URL=""

for candidate in \
  "http://127.0.0.1:7890" \
  "http://127.0.0.1:7897" \
  "http://127.0.0.1:6152" \
  "http://127.0.0.1:1087" \
  "http://127.0.0.1:8080" \
  "http://127.0.0.1:8888" \
  "socks5h://127.0.0.1:1080" \
  "socks5h://127.0.0.1:1086" \
  "socks5h://127.0.0.1:1087" \
  "socks5h://127.0.0.1:7890" \
  "socks5h://127.0.0.1:7891" \
  "socks5h://127.0.0.1:6153"
do
  if curl --silent --show-error --max-time 5 --proxy "$candidate" "https://www.baidu.com" >/dev/null 2>&1; then
    PROXY_URL="$candidate"
    break
  fi
done

if [ -n "$PROXY_URL" ]; then
  echo "Found proxy: $PROXY_URL"
  export HTTP_PROXY="$PROXY_URL"
  export HTTPS_PROXY="$PROXY_URL"
  export ALL_PROXY="$PROXY_URL"
  export http_proxy="$PROXY_URL"
  export https_proxy="$PROXY_URL"
  export all_proxy="$PROXY_URL"
else
  echo "No common local proxy port found. Starting with direct network."
fi

echo
echo "Testing historical market data endpoints..."
.venv/bin/python - <<'PY'
import urllib.request

tests = {
    "Eastmoney history": "https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=0.300502&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&klt=101&fqt=1&end=20500101&lmt=80",
    "Tencent history": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sz300502,day,,,90,qfq",
    "Sina history": "https://quotes.sina.cn/cn/api/json_v2.php/CN_MarketDataService.getKLineData?symbol=sz300502&scale=240&ma=no&datalen=90",
}

for name, url in tests.items():
    try:
        with urllib.request.urlopen(url, timeout=8) as response:
            data = response.read(120)
        print(f"OK   {name}: {len(data)} bytes")
    except Exception as error:
        print(f"FAIL {name}: {error}")
PY

echo
echo "Opening dashboard..."
open "http://localhost:${PORT}"
echo
echo "Keep this Terminal window open while using the dashboard."
echo "Press Control-C in this window to stop it."
echo

HOME="$PWD" .venv/bin/streamlit run app.py \
  --server.port "$PORT" \
  --server.address 127.0.0.1 \
  --server.headless true \
  --browser.gatherUsageStats false
