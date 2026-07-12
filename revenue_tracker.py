#!/usr/bin/env python3
"""
收入追踪器 (Revenue Tracker)
追踪所有收入来源，生成日报/周报，自动保存到反馈目录
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict

# ===== 配置 =====
BOT_DIR = Path("/Users/ai/Projects/task-bot")
EV_DIR = Path("/Users/ai/Projects/evolution-engine")
FEEDBACK_DIR = EV_DIR / "feedback"
FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)

REVENUE_LOG = FEEDBACK_DIR / "revenue_log.json"

# ===== 收入类型定义 =====
class RevenueSource:
    """收入来源枚举"""
    FREELANCE = "freelance"           # 接单收入
    AFFILIATE = "affiliate"           # 联盟营销
    DIGITAL_PRODUCT = "digital"       # 数字产品
    CONSULTING = "consulting"         # 咨询
    OTHER = "other"                   # 其他

# ===== 收入记录 =====
class RevenueEntry:
    def __init__(self, source: str, amount: float, currency: str = "CNY",
                 platform: str = "", description: str = "", tags: List[str] = None):
        self.timestamp = datetime.now().isoformat()
        self.source = source
        self.amount = amount
        self.currency = currency
        self.platform = platform
        self.description = description
        self.tags = tags or []

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "source": self.source,
            "amount": self.amount,
            "currency": self.currency,
            "platform": self.platform,
            "description": self.description,
            "tags": self.tags
        }

# ===== 收入追踪器主类 =====
class RevenueTracker:
    def __init__(self, log_path: Path = REVENUE_LOG):
        self.log_path = log_path
        self.entries: List[dict] = []
        self._load()

    def _load(self):
        """加载历史记录"""
        if self.log_path.exists():
            try:
                with open(self.log_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.entries = data.get('entries', [])
            except json.JSONDecodeError:
                self.entries = []
        else:
            self.entries = []

    def _save(self):
        """保存记录"""
        data = {
            "last_updated": datetime.now().isoformat(),
            "total_entries": len(self.entries),
            "entries": self.entries
        }
        with open(self.log_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add_entry(self, entry: RevenueEntry):
        """添加收入记录"""
        self.entries.append(entry.to_dict())
        self._save()

    def add(self, source: str, amount: float, currency: str = "CNY",
            platform: str = "", description: str = "", tags: List[str] = None):
        """快捷添加方法"""
        entry = RevenueEntry(source, amount, currency, platform, description, tags)
        self.add_entry(entry)

    def get_entries(self, days: int = 7, source: str = None) -> List[dict]:
        """获取最近 N 天的记录"""
        cutoff = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff.isoformat()

        filtered = [e for e in self.entries if e['timestamp'] >= cutoff_str]
        if source:
            filtered = [e for e in filtered if e['source'] == source]
        return filtered

    def get_daily_summary(self, days: int = 7) -> Dict[str, float]:
        """按天汇总收入"""
        daily = defaultdict(float)
        for entry in self.get_entries(days):
            date = entry['timestamp'][:10]  # YYYY-MM-DD
            amount = entry['amount']
            # 统一转换为 CNY (简化处理)
            if entry['currency'] == 'USD':
                amount *= 7.2  # 简化的汇率
            daily[date] += amount
        return dict(daily)

    def get_source_summary(self, days: int = 7) -> Dict[str, Dict]:
        """按收入来源汇总"""
        sources = defaultdict(lambda: {"total": 0, "count": 0, "platforms": set()})

        for entry in self.get_entries(days):
            src = entry['source']
            sources[src]['total'] += entry['amount']
            sources[src]['count'] += 1
            if entry.get('platform'):
                sources[src]['platforms'].add(entry['platform'])

        # 转换 set 为 list
        return {k: {**v, 'platforms': list(v['platforms'])} for k, v in sources.items()}

    def get_total(self, days: int = 7) -> float:
        """计算总收入"""
        return sum(e['amount'] for e in self.get_entries(days))

    def get_conversion_rate(self) -> Dict[str, float]:
        """计算转化率 (从联盟点击到收入)"""
        # 读取联盟点击数据
        clicks_path = EV_DIR / "metrics" / "affiliate_clicks.json"
        conversions_path = EV_DIR / "metrics" / "affiliate_conversions.json"

        clicks = 0
        conversions = 0

        if clicks_path.exists():
            with open(clicks_path, 'r') as f:
                data = json.load(f)
                for key, val in data.items():
                    if isinstance(val, dict) and 'values' in val:
                        clicks += sum(v.get('v', 0) for v in val['values'])
                    else:
                        clicks += val if isinstance(val, (int, float)) else 0

        if conversions_path.exists():
            with open(conversions_path, 'r') as f:
                data = json.load(f)
                for key, val in data.items():
                    if isinstance(val, dict) and 'values' in val:
                        conversions += sum(v.get('v', 0) for v in val['values'])
                    else:
                        conversions += val if isinstance(val, (int, float)) else 0

        rate = (conversions / clicks * 100) if clicks > 0 else 0
        return {"clicks": clicks, "conversions": conversions, "rate": rate}

    def generate_daily_report(self) -> str:
        """生成每日报告"""
        today = datetime.now().strftime('%Y-%m-%d')
        today_entries = self.get_entries(days=1)

        lines = [
            "=" * 50,
            "每日收入报告",
            f"   {today}",
            "=" * 50,
            ""
        ]
        today_total = sum(e['amount'] for e in today_entries)
        lines.append(f"📊 今日总收入: ¥{today_total:.2f}")
        lines.append(f"   收入笔数: {len(today_entries)} 笔")
        lines.append("")

        # 按来源细分
        if today_entries:
            by_source = defaultdict(float)
            for e in today_entries:
                by_source[e['source']] += e['amount']

            lines.append("📋 收入来源明细:")
            for src, amt in sorted(by_source.items(), key=lambda x: -x[1]):
                icon = {"freelance": "💼", "affiliate": "🔗", "digital": "📦",
                        "consulting": "💡", "other": "📝"}.get(src, "•")
                lines.append(f"   {icon} {src}: ¥{amt:.2f}")
            lines.append("")

        # 本周趋势
        week_daily = self.get_daily_summary(days=7)
        if week_daily:
            lines.append("📈 本周趋势 (CNY):")
            for date, amount in sorted(week_daily.items()):
                bar = "█" * int(amount / 100) if amount > 0 else "░"
                lines.append(f"   {date}: {bar} ¥{amount:.0f}")
            lines.append("")
            lines.append(f"📊 本周总收入: ¥{self.get_total(7):.2f}")
            week_avg = self.get_total(7) / 7
            lines.append(f"   日均: ¥{week_avg:.2f}")

        # 联盟转化
        conv = self.get_conversion_rate()
        if conv['clicks'] > 0:
            lines.append("")
            lines.append("🔗 联盟转化:")
            lines.append(f"   点击: {conv['clicks']}, 转化: {conv['conversions']}")
            lines.append(f"   转化率: {conv['rate']:.2f}%")

        lines.append("")
        lines.append("=" * 50)

        return "\n".join(lines)

    def generate_weekly_report(self) -> str:
        """生成周报"""
        week_start = (datetime.now() - timedelta(days=6)).strftime('%Y-%m-%d')
        week_end = datetime.now().strftime('%Y-%m-%d')

        week_total = self.get_total(7)
        source_summary = self.get_source_summary(7)

        lines = [
            "=" * 60,
            "📅 周报摘要",
            f"   {week_start} ~ {week_end}",
            "=" * 60,
            ""
        ]

        # 总体收入
        lines.append(f"💰 本周总收入: ¥{week_total:.2f}")

        # 按来源
        lines.append("")
        lines.append("📊 收入来源分布:")
        if source_summary:
            for src, data in sorted(source_summary.items(), key=lambda x: -x[1]['total']):
                icon = {"freelance": "💼", "affiliate": "🔗", "digital": "📦",
                        "consulting": "💡", "other": "📝"}.get(src, "•")
                pct = (data['total'] / week_total * 100) if week_total > 0 else 0
                lines.append(f"   {icon} {src}: ¥{data['total']:.2f} ({pct:.1f}%) x{data['count']}笔")
                if data['platforms']:
                    lines.append(f"      平台: {', '.join(data['platforms'])}")
        else:
            lines.append("   (暂无数据)")

        # 每日趋势
        daily = self.get_daily_summary(7)
        if daily:
            lines.append("")
            lines.append("📈 每日收入:")
            for date, amount in sorted(daily.items()):
                bar = "█" * min(int(amount / 50), 30)
                lines.append(f"   {date}: {bar} ¥{amount:.0f}")

        # 目标对比
        weekly_goal = 7000  # 每周目标
        progress = (week_total / weekly_goal * 100)
        lines.append("")
        lines.append(f"🎯 目标进度: {progress:.1f}% (目标 ¥{weekly_goal})")
        if progress >= 100:
            lines.append("   ✅ 超额完成!")
        elif progress >= 70:
            lines.append("   🔄 正常进行")
        else:
            lines.append("   ⚠️ 需要加强")

        # 转化率
        conv = self.get_conversion_rate()
        if conv['clicks'] > 0:
            lines.append("")
            lines.append(f"🔗 联盟转化: {conv['rate']:.2f}% ({conv['conversions']}/{conv['clicks']})")

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)

    def generate_insights(self) -> List[Dict]:
        """生成优化洞察"""
        insights = []
        source_summary = self.get_source_summary(30)
        week_total = self.get_total(7)

        if not source_summary:
            return [{"type": "info", "message": "数据不足，暂无洞察"}]

        # 找出最佳收入来源
        if source_summary:
            best_source = max(source_summary.items(), key=lambda x: x[1]['total'])
            insights.append({
                "type": "win",
                "source": best_source[0],
                "message": f"💎 {best_source[0]} 是最佳收入来源 (¥{best_source[1]['total']:.0f})",
                "action": "加大对最佳来源的投入"
            })

        # 检测下滑
        daily = self.get_daily_summary(7)
        if len(daily) >= 2:
            dates = sorted(daily.keys())
            recent = daily[dates[-1]]
            prev = daily[dates[-2]]
            if recent < prev * 0.5:
                insights.append({
                    "type": "warning",
                    "message": f"⚠️ 今日收入下降 {((1 - recent/prev)*100):.0f}%",
                    "action": "检查是否有技术问题或市场变化"
                })

        # 转化率优化
        conv = self.get_conversion_rate()
        if conv['rate'] < 2 and conv['clicks'] > 10:
            insights.append({
                "type": "improve",
                "message": f"🔧 联盟转化率偏低 ({conv['rate']:.2f}%)",
                "action": "测试不同的推广文案和着陆页"
            })

        return insights


# ===== CLI 入口 =====
def main():
    import argparse
    parser = argparse.ArgumentParser(description='收入追踪器')
    parser.add_argument('--add', nargs=3, metavar=('SOURCE', 'AMOUNT', 'DESC'),
                       help='添加收入记录: python revenue_tracker.py --add freelance 500 "测试项目"')
    parser.add_argument('--daily', action='store_true', help='生成日报')
    parser.add_argument('--weekly', action='store_true', help='生成周报')
    parser.add_argument('--insights', action='store_true', help='生成洞察')
    parser.add_argument('--list', action='store_true', help='列出最近记录')
    parser.add_argument('--days', type=int, default=7, help='统计天数(默认7)')

    args = parser.parse_args()

    tracker = RevenueTracker()

    # 添加记录
    if args.add:
        source, amount, desc = args.add
        tracker.add(source, float(amount), description=desc)
        print(f"✅ 已添加: {source} ¥{amount} - {desc}")
        return

    # 生成报告
    if args.daily:
        print(tracker.generate_daily_report())
        return

    if args.weekly:
        print(tracker.generate_weekly_report())
        return

    if args.insights:
        insights = tracker.generate_insights()
        print("💡 优化洞察:")
        for i in insights:
            print(f"   {i.get('message', i)}")
        return

    if args.list:
        entries = tracker.get_entries(days=args.days)
        print(f"📋 最近 {args.days} 天记录 ({len(entries)} 笔):")
        for e in entries[-10:]:
            print(f"   {e['timestamp'][:10]} | {e['source']} | ¥{e['amount']} | {e.get('description','')}")
        return

    # 默认显示日报
    print(tracker.generate_daily_report())


if __name__ == "__main__":
    main()