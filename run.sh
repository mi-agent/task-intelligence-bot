#!/bin/bash
# Task Intelligence Bot - 一键运行脚本
# 用法: bash run.sh

VENV_PYTHON="$HOME/.hermes/hermes-agent/venv/bin/python"
BOT_DIR="$HOME/Projects/task-bot"
LOG_DIR="$BOT_DIR/data"
LOG_FILE="$LOG_DIR/bot_run.log"

echo "🚀 Task Intelligence Bot 启动..."
echo "📅 $(date '+%Y-%m-%d %H:%M:%S')"

mkdir -p "$LOG_DIR"

# 1. 爬取任务
echo ""
echo "📡 [1/3] 爬取任务平台..."
$VENV_PYTHON "$BOT_DIR/task_scraper_v2.py" 2>&1 | tee -a "$LOG_FILE"

# 2. 生成内容
echo ""
echo "📝 [2/3] 生成内容营销素材..."
$VENV_PYTHON "$BOT_DIR/content_marketing.py" 2>&1 | tee -a "$LOG_FILE"

# 3. 推送通知（默认仅保存）
echo ""
echo "💬 [3/3] 推送通知..."
$VENV_PYTHON "$BOT_DIR/notifiers/notifier.py" --save 2>&1 | tee -a "$LOG_FILE"

echo ""
echo "✅ 完成！查看输出："
echo "   📊 任务数据: $BOT_DIR/data/latest_final.json"
echo "   📝 内容:     $BOT_DIR/content/latest_*.md"
echo "   💬 推送:     $BOT_DIR/notifiers/telegram_*.txt"
echo "   📜 日志:     $LOG_FILE"