#!/bin/zsh
set -e

cd "$(dirname "$0")"

echo "AI产业链投资驾驶舱 - 上传到 GitHub"
echo

echo "正在检查 GitHub SSH 连接..."
ssh -T git@github.com || true
echo

echo "正在设置 GitHub 远程地址..."
git remote set-url origin git@github.com:gqq739025187-ctrl/ai-industry-dashboard.git

echo
echo "正在检查本地改动..."
git status --short

echo
echo "正在加入本次要上传的文件..."
git add -A

echo
echo "正在提交本地文件..."
if git diff --cached --quiet; then
  echo "没有新的文件需要提交。"
else
  git commit -m "Update AI industry dashboard"
fi

echo
echo "正在上传到 GitHub..."
git push -u origin main

echo
echo "上传完成。当前状态："
git status --short

echo
echo "请打开 GitHub 仓库确认文件已经出现："
echo "https://github.com/gqq739025187-ctrl/ai-industry-dashboard"
echo
echo "按回车键关闭窗口。"
read
