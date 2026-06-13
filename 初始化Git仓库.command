#!/bin/zsh
cd "$(dirname "$0")" || exit 1

echo "正在初始化 Git 仓库..."

if [ ! -d ".git" ]; then
  git init
fi

if ! git config user.name >/dev/null; then
  echo ""
  echo "Git 还没有设置用户名。"
  echo "请输入你的名字，例如：xiaogutongxue"
  read "GIT_NAME?Git 用户名: "
  git config user.name "$GIT_NAME"
fi

if ! git config user.email >/dev/null; then
  echo ""
  echo "Git 还没有设置邮箱。"
  echo "请输入你的 GitHub 邮箱。"
  read "GIT_EMAIL?Git 邮箱: "
  git config user.email "$GIT_EMAIL"
fi

git add .

if git diff --cached --quiet; then
  echo "没有新的文件需要提交。"
else
  git commit -m "Initial commit"
fi

echo ""
echo "完成。下一步请去 GitHub 创建一个空仓库，然后按 README 或 Codex 给你的步骤 push。"
echo "按回车关闭窗口。"
read
