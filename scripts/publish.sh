#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${1:-}"
if [[ -z "$REPO_URL" ]]; then
  echo "用法: bash scripts/publish.sh <repo_url>"
  exit 1
fi

if ! command -v git >/dev/null 2>&1; then
  echo "未偵測到 git，請先安裝 git"
  exit 1
fi

if [[ ! -d .git ]]; then
  git init
fi

git add -A
git commit -m "feat: 初始化金融科技系統（回測/視覺化/風險模型）" || true

git branch -M main || true

if ! git remote | grep -q origin; then
  git remote add origin "$REPO_URL"
else
  git remote set-url origin "$REPO_URL"
fi

git push -u origin main
echo "推送完成：$REPO_URL"
