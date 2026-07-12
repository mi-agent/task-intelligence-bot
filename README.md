# Task Intelligence Bot 🤖

> Automated task/freelance opportunity scraper + content marketing generator.

## 功能
- 🕷️ 爬取 5+ 远程工作平台（远程.work / WWR / RemoteOK / 电鸭 / 程序员客栈）
- 📝 自动生成知乎/掘金/微信/联盟营销内容
- 💬 Telegram/Discord 推送通知
- ⏰ 每日 08:00 自动运行（北京时间）

## 快速开始

```bash
# 一键运行完整 pipeline
bash run.sh

# 单独运行
python task_scraper_v2.py   # 爬取任务
python content_marketing.py # 生成内容
python notifiers/notifier.py --telegram  # 推送
```

## 定时任务（本地 macOS/Linux）

```bash
crontab -e
# 每天早上 8 点运行
0 8 * * * cd ~/Projects/task-bot && bash run.sh >> data/bot_run.log 2>&1
```

## 项目结构

```
task-bot/
├── task_scraper_v2.py      # 任务爬虫核心
├── content_marketing.py    # 内容生成器
├── notifiers/
│   └── notifier.py         # 推送机器人（Telegram/Discord）
├── content/                 # 生成的内容素材
│   ├── latest_zhihu.md
│   ├── latest_juejin.md
│   ├── latest_affiliate.md
│   └── latest_wechat.html
├── data/                   # 任务数据
│   └── latest_final.json
└── run.sh                  # 一键运行脚本
```

## 变现路径

1. 接单赚钱：整理的任务列表 → 自己挑着接
2. 内容变现：生成的知乎/掘金文章 → 积累粉丝 → 变现
3. 联盟营销：文章中嵌入联盟链接 → 被动收入
4. 工具 SaaS：把爬虫系统包装成服务 → 月订阅

## 最近任务示例


> 共 22 条任务（20260712_0838）

- **远程.work** Python后端开发工程师 | 15k-25k
- **远程.work** Python 软件工程师 | 15k-25k
- **远程.work** fullstack工程师 | 5k-10k
- **远程.work** Python /shell 自动化脚本工程师 | 15k-25k
- **远程.work** web3 社交项目-高级安全专家 | 25k-50k
- **远程.work** 高级 Python 全栈开发工程师 | 15k-25k
- **远程.work** 高级 Python 工程师 | 25k-50k
- **远程.work** 运维工程师 - 去中心化交易所 | 25k-50k

---
Built with Crawl4AI + Python | Zero cost | Fully automated
