#!/bin/zsh
set -e

cd "$(dirname "$0")"

PORT=8503

echo "正在从普通终端启动 AI 投资驾驶舱..."
echo
echo "访问地址：http://localhost:${PORT}"
echo

echo "正在检查当前终端网络..."
.venv/bin/python - <<'PY'
import socket

for host in ["www.baidu.com", "push2his.eastmoney.com", "qt.gtimg.cn"]:
    try:
        ip = socket.gethostbyname(host)
        print(f"成功  {host} -> {ip}")
    except Exception as error:
        print(f"失败  {host} -> {error}")
PY

echo
echo "正在寻找本机代理端口..."
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
  echo "找到可用代理：$PROXY_URL"
  export HTTP_PROXY="$PROXY_URL"
  export HTTPS_PROXY="$PROXY_URL"
  export ALL_PROXY="$PROXY_URL"
  export http_proxy="$PROXY_URL"
  export https_proxy="$PROXY_URL"
  export all_proxy="$PROXY_URL"
else
  echo "没有找到常见本机代理端口。将直接连接。"
fi

echo
echo "正在测试历史行情接口..."
.venv/bin/python - <<'PY'
import urllib.request

tests = {
    "东方财富历史": "https://push2his.eastmoney.com/api/qt/stock/kline/get?secid=0.300502&fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61&klt=101&fqt=1&end=20500101&lmt=80",
    "腾讯历史": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param=sz300502,day,,,90,qfq",
    "新浪历史": "https://quotes.sina.cn/cn/api/json_v2.php/CN_MarketDataService.getKLineData?symbol=sz300502&scale=240&ma=no&datalen=90",
}

for name, url in tests.items():
    try:
        with urllib.request.urlopen(url, timeout=8) as response:
            data = response.read(120)
        print(f"成功  {name}：{len(data)} 字节")
    except Exception as error:
        print(f"失败  {name}：{error}")
PY

echo
echo "浏览器即将打开驾驶舱。使用期间请不要关闭这个终端窗口。"
open "http://localhost:${PORT}"
echo

HOME="$PWD" .venv/bin/streamlit run app.py \
  --server.port "$PORT" \
  --server.address 127.0.0.1 \
  --server.headless true \
  --browser.gatherUsageStats false
