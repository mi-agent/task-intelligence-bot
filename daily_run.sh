#!/bin/bash
# 每日 /Users/ai/.hermes/hermes-agent/venv/bin/python 自动化任务
# 自动运行：任务爬取 → 内容生成 → 进化分析 → 收入记录

BOT_DIR="$HOME/Projects/task-bot"
EV_DIR="$HOME/Projects/evolution-engine"
LOG="$BOT_DIR/data/bot_run.log"

echo "=== $(date '+%Y-%m-%d %H:%M:%S') ===" >> "$LOG"
cd "$BOT_DIR"

# 1. 运行任务爬虫 v3（带后备数据）
echo "🕷️ 开始任务采集..." >> "$LOG"
/Users/ai/.hermes/hermes-agent/venv/bin/python "$BOT_DIR/task_scraper_v3.py" >> "$LOG" 2>&1

# 2. 运行 SEO 优化
echo "🔍 运行 SEO 优化..." >> "$LOG"
/Users/ai/.hermes/hermes-agent/venv/bin/python "$BOT_DIR/seo_optimizer.py" >> "$LOG" 2>&1

# 3. 运行进化引擎
echo "🧬 运行进化引擎..." >> "$LOG"
/Users/ai/.hermes/hermes-agent/venv/bin/python "$EV_DIR/evolution.py" >> "$LOG" 2>&1

# 4. 运行反馈学习
echo "📊 运行反馈学习..." >> "$LOG"
/Users/ai/.hermes/hermes-agent/venv/bin/python "$BOT_DIR/feedback_learner.py" >> "$LOG" 2>&1

# 5. 运行收入追踪
echo "💰 运行收入追踪..." >> "$LOG"
/Users/ai/.hermes/hermes-agent/venv/bin/python "$BOT_DIR/revenue_tracker.py" --log >> "$LOG" 2>&1

echo "✅ 每日任务完成 $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG"
