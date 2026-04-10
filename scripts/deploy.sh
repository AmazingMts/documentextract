#!/bin/bash
# deploy.sh — 爬取 + 摘要 + 构建前端 + 推送到 GitHub Pages
# 用法: ./scripts/deploy.sh
# 定时用法 (crontab): 0 7 * * * /path/to/scripts/deploy.sh >> /tmp/distsys_deploy.log 2>&1

set -e  # 任意一步失败则退出

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
VENV="$BACKEND_DIR/.venv/bin/python3"

echo "======================================"
echo "DistSys Feed Deploy — $(date '+%Y-%m-%d %H:%M:%S')"
echo "======================================"

# ── 1. 爬取 ──────────────────────────────
echo "[1/4] 爬取新文章..."
cd "$BACKEND_DIR"
"$VENV" -c "
import asyncio
from app.crawler.pipeline import run_crawl_pipeline
asyncio.run(run_crawl_pipeline())
"

# ── 2. 摘要（处理所有 pending 文章）───────
echo "[2/4] 生成 AI 摘要..."
# 循环直到没有 pending 文章
while true; do
  PENDING=$("$VENV" -c "
import asyncio
from app.database import init_db, AsyncSessionLocal
from app.models import Article
from sqlalchemy import select, func
async def count():
    await init_db()
    async with AsyncSessionLocal() as s:
        return await s.scalar(select(func.count()).select_from(Article).where(Article.status=='pending').where(Article.is_relevant==True))
print(asyncio.run(count()))
")
  if [ "$PENDING" -eq 0 ]; then
    break
  fi
  echo "  → $PENDING 篇待摘要..."
  "$VENV" -c "
import asyncio
from app.summarizer.pipeline import run_summarization_pipeline
asyncio.run(run_summarization_pipeline())
"
done

# ── 3. 导出 JSON + 构建前端 ──────────────
echo "[3/4] 导出 articles.json 并构建前端..."

# 提前获取 remote，构建时需要仓库名作为 base path
REMOTE=$(git -C "$PROJECT_DIR" remote get-url origin 2>/dev/null || echo "")
if [ -z "$REMOTE" ]; then
  echo "错误：项目没有设置 git remote origin，请先运行："
  echo "  git remote add origin https://github.com/你的用户名/你的仓库名.git"
  exit 1
fi

"$VENV" "$SCRIPT_DIR/export_articles.py"

cd "$FRONTEND_DIR"
REPO_PATH=$(basename "$REMOTE" .git)
VITE_BASE_PATH="/${REPO_PATH}/" npm run build --silent

# ── 4. 推送到 gh-pages 分支 ──────────────
echo "[4/4] 推送到 GitHub Pages..."
cd "$FRONTEND_DIR/dist"

# 初始化一个临时 git repo 只包含 dist 内容
git init -q
git checkout -q -b gh-pages
git add -A
git commit -q -m "deploy: $(date '+%Y-%m-%d %H:%M')"

# 推送到远端（强制覆盖 gh-pages 分支）
if [ -z "$REMOTE" ]; then
  echo "错误：项目没有设置 git remote origin，请先运行："
  echo "  git remote add origin https://github.com/你的用户名/你的仓库名.git"
  exit 1
fi
git remote add origin "$REMOTE"
git push -q --force origin gh-pages

# 清理临时 git
cd "$PROJECT_DIR"

echo ""
echo "✓ 部署完成！"
GITHUB_USER=$(echo "$REMOTE" | sed 's|.*github.com[:/]\([^/]*\)/.*|\1|')
echo "  网页地址: https://${GITHUB_USER}.github.io/${REPO_PATH}/"
echo "======================================"
