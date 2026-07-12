#!/usr/bin/env python3
"""
Notifier Bot - Telegram/Discord 推送机器人
"""
import json, os, time, argparse
from pathlib import Path
from datetime import datetime

DATA_DIR = Path("/Users/ai/Projects/task-bot/data")
OUT_DIR = Path("/Users/ai/Projects/task-bot/notifiers")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ============ Telegram Bot ============
def load_config():
    cfg_file = OUT_DIR / "config.json"
    if cfg_file.exists():
        with open(cfg_file) as f:
            return json.load(f)
    return {}

def save_config(cfg):
    cfg_file = OUT_DIR / "config.json"
    with open(cfg_file, "w") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

def load_jobs():
    paths = [
        DATA_DIR / "latest_final.json",
        DATA_DIR / "latest_v2.json",
    ]
    for p in paths:
        if p.exists():
            with open(p) as f:
                return json.load(f)
    return {"total": 0, "jobs": []}

def format_telegram(data: dict) -> str:
    jobs = data.get("jobs", [])
    if not jobs:
        return f"🤖 任务速报 | {data.get('scraped_at', datetime.now().strftime('%Y-%m-%d %H:%M'))}\n\n暂无新任务，稍后再试"
    
    by_platform = {}
    for j in jobs:
        by_platform.setdefault(j["platform"], []).append(j)
    
    lines = [
        f"🤖 <b>任务情报</b> | {data.get('scraped_at', '')}",
        f"📊 <b>{len(jobs)}条</b>优质任务 | {len(by_platform)}个平台\n",
    ]
    
    for platform, pjobs in list(by_platform.items())[:3]:
        lines.append(f"🏷️ <b>{platform}</b>")
        for j in pjobs[:4]:
            lang = "🌐" if j.get("lang") == "en" else "🇨🇳"
            has_price = any(c in str(j.get("salary","")) for c in "0123456789$¥￥")
            emoji = "💰" if has_price else "📋"
            lines.append(
                f"{emoji} <b>{j['title'][:50]}</b>\n"
                f"   {j['salary']} | {j.get('company','')}\n"
                f"   → {j['url'][:60]}"
            )
        lines.append("")
    
    lines.append(f"<i>还有 {max(0,len(jobs)-12)} 条，回复「完整」获取完整列表</i>")
    return "\n".join(lines)

def format_discord(data: dict) -> str:
    jobs = data.get("jobs", [])
    if not jobs:
        return f"🤖 任务速报 | {data.get('scraped_at', '')}\n\n暂无新任务"
    
    lines = [
        f"## 🤖 任务情报 | {data.get('scraped_at', '')}",
        f"**{len(jobs)} 条**优质任务 | {len(set(j['platform'] for j in jobs))} 个平台\n",
    ]
    
    for j in jobs[:8]:
        lang = "🌐" if j.get("lang") == "en" else "🇨🇳"
        lines.append(
            f"**{lang} {j['title'][:50]}**\n"
            f"💰 {j['salary']} | 🏢 {j.get('company', '知名公司')}\n"
            f"🔗 {j['url']}"
        )
        lines.append("")
    
    return "\n".join(lines)

def send_telegram(message: str, bot_token: str = None, chat_id: str = None) -> bool:
    if not bot_token or not chat_id:
        cfg = load_config()
        bot_token = bot_token or cfg.get("telegram_bot_token")
        chat_id = chat_id or cfg.get("telegram_chat_id")
    
    if not bot_token:
        print("  ⚠️  未配置 Telegram Bot Token，消息已保存但未发送")
        return False
    
    import urllib.request
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = json.dumps({
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }).encode()
    
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            resp = json.loads(r.read())
            if resp.get("ok"):
                print(f"  ✅ Telegram 发送成功 (msg_id: {resp['result']['message_id']})")
                return True
            else:
                print(f"  ❌ Telegram 错误: {resp}")
                return False
    except Exception as e:
        print(f"  ❌ Telegram 异常: {e}")
        return False

def send_discord(message: str, webhook_url: str = None) -> bool:
    if not webhook_url:
        cfg = load_config()
        webhook_url = cfg.get("discord_webhook")
    
    if not webhook_url:
        print("  ⚠️  未配置 Discord Webhook，消息已保存但未发送")
        return False
    
    import urllib.request
    data = json.dumps({"content": message}).encode()
    req = urllib.request.Request(webhook_url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10):
            print(f"  ✅ Discord 发送成功")
            return True
    except Exception as e:
        print(f"  ❌ Discord 异常: {e}")
        return False

def save_message(message: str, channel: str):
    """Save message to file for reference"""
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    path = OUT_DIR / f"{channel}_{ts}.txt"
    with open(path, "w", encoding="utf-8") as f:
        f.write(message)
    print(f"  💾 已保存: {path}")

# ============ 主程序 ============
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Notifier Bot")
    parser.add_argument("--telegram", action="store_true", help="发送 Telegram")
    parser.add_argument("--discord", action="store_true", help="发送 Discord")
    parser.add_argument("--save", action="store_true", help="仅保存消息")
    parser.add_argument("--bot-token", help="Telegram Bot Token")
    parser.add_argument("--chat-id", help="Telegram Chat ID")
    parser.add_argument("--webhook", help="Discord Webhook URL")
    parser.add_argument("--setup", action="store_true", help="设置配置")
    args = parser.parse_args()
    
    print("💬 Notifier Bot 启动...\n")
    
    if args.setup:
        # Interactive setup
        print("=== 配置 Telegram Bot ===")
        bot_token = input("Bot Token (ghp_xxx 格式): ").strip()
        chat_id = input("Chat ID (你的 Telegram user_id 或群组ID): ").strip()
        print("\n=== 配置 Discord Webhook ===")
        webhook = input("Discord Webhook URL: ").strip()
        
        save_config({
            "telegram_bot_token": bot_token,
            "telegram_chat_id": chat_id,
            "discord_webhook": webhook,
        })
        print("\n✅ 配置已保存！")
    else:
        # Load data and send
        data = load_jobs()
        print(f"📊 加载 {data['total']} 条任务")
        
        tg_msg = format_telegram(data)
        dc_msg = format_discord(data)
        
        # Save both
        save_message(tg_msg, "telegram")
        save_message(dc_msg, "discord")
        
        # Send
        if args.save:
            print("\n✅ 消息已保存（未发送）")
        else:
            sent = []
            if args.telegram or (not args.telegram and not args.discord):
                if send_telegram(tg_msg, args.bot_token, args.chat_id):
                    sent.append("Telegram")
            
            if args.discord or (not args.telegram and not args.discord):
                if send_discord(dc_msg, args.webhook):
                    sent.append("Discord")
            
            if not sent:
                print("\n⚠️  未发送任何消息（需要先配置或加 --telegram/--discord 参数）")
                print("   运行以下命令配置：")
                print("   python3 ~/Projects/task-bot/notifiers/notifier.py --setup")