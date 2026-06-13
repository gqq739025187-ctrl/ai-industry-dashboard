#!/bin/zsh
cd "$(dirname "$0")" || exit 1

echo "AI产业链投资驾驶舱 - 上传到 GitHub"
echo ""

if ! command -v git >/dev/null 2>&1; then
  echo "没有找到 git。请先安装 Xcode Command Line Tools。"
  echo "按回车关闭窗口。"
  read
  exit 1
fi

if [ ! -d ".git" ]; then
  echo "当前文件夹还不是 Git 仓库，正在初始化..."
  git init
fi

if ! git config user.name >/dev/null; then
  echo ""
  echo "Git 还没有设置用户名。"
  read "GIT_NAME?请输入你的 Git 用户名: "
  git config user.name "$GIT_NAME"
fi

if ! git config user.email >/dev/null; then
  echo ""
  echo "Git 还没有设置邮箱。"
  read "GIT_EMAIL?请输入你的 GitHub 邮箱: "
  git config user.email "$GIT_EMAIL"
fi

REMOTE_URL=$(git remote get-url origin 2>/dev/null)
if [ -z "$REMOTE_URL" ]; then
  echo ""
  echo "请输入你的 GitHub 仓库地址。"
  echo "格式类似：https://github.com/你的用户名/ai-industry-dashboard.git"
  read "REMOTE_URL?GitHub 仓库地址: "
  git remote add origin "$REMOTE_URL"
else
  echo "已找到 GitHub 远端：$REMOTE_URL"
fi

echo ""
echo "正在检查要上传的文件..."
git status --short

echo ""
echo "正在提交本地文件..."
git add .

if git diff --cached --quiet; then
  echo "没有新的文件需要提交。"
else
  git commit -m "Initial commit"
fi

echo ""
echo "正在设置 main 分支..."
git branch -M main

echo ""
echo "正在上传到 GitHub..."
git push -u origin main

echo ""
echo "上传流程结束。"
echo "如果上方没有 error/fatal，说明已经上传成功。"
echo "按回车关闭窗口。"
read
