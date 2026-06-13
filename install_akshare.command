#!/bin/zsh
set -e

cd "$(dirname "$0")"

echo "Installing AkShare into this project's Python environment..."
echo

.venv/bin/python -m pip install --upgrade akshare -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com

echo
echo "Verifying AkShare..."
.venv/bin/python - <<'PY'
import akshare as ak
print("AkShare installed:", ak.__version__)
PY

echo
echo "Done. You can refresh http://localhost:8502 after restarting Streamlit."
echo "Press Enter to close this window."
read
