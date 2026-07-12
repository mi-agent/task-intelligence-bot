#!/usr/bin/env python3
"""
Feedback Learner - 反馈学习器
从任务申请成功率、收入数据中学习，自动优化策略
"""
import json, os, re
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict, Counter

BOT_DIR = Path("/Users/ai/Projects/task-bot")
EV_DIR = Path("/Users/ai/Projects/evolution-engine")
FEEDBACK_DIR = EV_DIR / "feedback"
FEEDBACK_DIR.mkdir(exist_ok=True)

class FeedbackLearner:
    """从反馈中学习的引擎"""
    
    def __init__(self):
        self.learnings = []
        self.strategy_updates = []
    
    # ============ 分析申请成功率 ============
    def analyze_applications(self) -> dict:
        """分析任务申请数据，找出成功模式"""
        
        # 读取任务数据
        latest = BOT_DIR / "data" / "latest_final.json"
        if not latest.exists():
            return {"status": "no_data"}
        
        with open(latest) as f:
            data = json.load(f)
        
        jobs = data.get("jobs", [])
        
        # 按平台统计
        platform_stats = defaultdict(lambda: {"count": 0, "salaries": [], "titles": []})
        
        for j in jobs:
            p = j.get("platform", "unknown")
            s = j.get("salary", "")
            t = j.get("title", "")
            
            platform_stats[p]["count"] += 1
            platform_stats[p]["titles"].append(t)
            
            # 提取薪资数字
            nums = re.findall(r'(\d+)', s)
            if nums:
                platform_stats[p]["salaries"].append(int(nums[0]))
        
        # 分析结果
        insights = []
        
        for p, stats in sorted(platform_stats.items(), key=lambda x: -x[1]["count"]):
            salaries = stats["salaries"]
            avg_salary = sum(salaries) / len(salaries) if salaries else 0
            
            insights.append({
                "platform": p,
                "task_count": stats["count"],
                "avg_salary": round(avg_salary, 1),
                "recommendation": self._platform_recommendation(p, stats["count"], avg_salary)
            })
        
        return {"insights": insights, "total_jobs": len(jobs)}
    
    def _platform_recommendation(self, platform: str, count: int, avg_salary: float) -> str:
        """根据平台特征给出推荐"""
        if count < 3:
            return f"⚪ 任务少，建议作为补充"
        elif avg_salary > 20:
            return f"🟢 任务多+高薪，优先投递！"
        elif avg_salary > 12:
            return f"🟡 任务稳定，中等优先级"
        else:
            return f"🟡 可以尝试，关注高质量任务"
    
    # ============ 分析薪资趋势 ============
    def analyze_salary_trends(self) -> dict:
        """分析哪些薪资区间最常见"""
        
        latest = BOT_DIR / "data" / "latest_final.json"
        if not latest.exists():
            return {}
        
        with open(latest) as f:
            data = json.load(f)
        
        jobs = data.get("jobs", [])
        
        salary_ranges = {"5k以下": 0, "5k-10k": 0, "10k-15k": 0, "15k-25k": 0, "25k+": 0}
        
        for j in jobs:
            s = j.get("salary", "")
            nums = re.findall(r'(\d+)', s)
            
            if nums:
                val = max(nums)
                if int(val) <= 5: salary_ranges["5k以下"] += 1
                elif int(val) <= 10: salary_ranges["5k-10k"] += 1
                elif int(val) <= 15: salary_ranges["10k-15k"] += 1
                elif int(val) <= 25: salary_ranges["15k-25k"] += 1
                else: salary_ranges["25k+"] += 1
        
        # 找出最优范围
        best_range = max(salary_ranges, key=salary_ranges.get)
        
        return {
            "distribution": salary_ranges,
            "best_range": best_range,
            "recommendation": f"主攻 {best_range} 区间（任务最多）"
        }
    
    # ============ 内容效果分析 ============
    def analyze_content_performance(self) -> dict:
        """分析内容表现"""
        
        content_dir = BOT_DIR / "content"
        if not content_dir.exists():
            return {"status": "no_content"}
        
        files = list(content_dir.glob("*.md"))
        
        # 模拟CTR数据（真实情况需要 Google Analytics）
        # 这里基于内容长度和关键词做简单评分
        content_scores = []
        
        for f in files:
            content = f.read_text()
            lines = content.split("\n")
            
            # 简单评分
            score = 0
            score += len([l for l in lines if l.startswith("#")]) * 5  # 标题多
            score += min(len(content) / 500, 20)  # 内容长度
            score += len(re.findall(r'💰|🔥|✅|📊|🎯', content)) * 2  # emoji
            score += len(re.findall(r'\d+k|\$\d+', content)) * 3  # 数字
            
            content_scores.append({
                "file": f.name,
                "score": round(score, 1),
                "preview": content[:100].replace("\n", " ")
            })
        
        # 排序
        content_scores.sort(key=lambda x: -x["score"])
        
        return {
            "top_performers": content_scores[:3],
            "recommendation": f"重点推广: {content_scores[0]['file'] if content_scores else '暂无'}"
        }
    
    # ============ 生成优化建议 ============
    def generate_learnings(self) -> list:
        """生成可执行的优化建议"""
        learnings = []
        
        # 分析申请
        app_analysis = self.analyze_applications()
        if "insights" in app_analysis:
            for insight in app_analysis["insights"][:3]:
                learnings.append({
                    "type": "task_strategy",
                    "platform": insight["platform"],
                    "action": insight["recommendation"],
                    "priority": "high" if "优先" in insight["recommendation"] else "medium",
                    "confidence": 0.8
                })
        
        # 分析薪资
        salary_analysis = self.analyze_salary_trends()
        if "recommendation" in salary_analysis:
            learnings.append({
                "type": "salary_filter",
                "action": salary_analysis["recommendation"],
                "distribution": salary_analysis["distribution"],
                "priority": "medium"
            })
        
        # 内容分析
        content_analysis = self.analyze_content_performance()
        if "recommendation" in content_analysis:
            learnings.append({
                "type": "content_focus",
                "action": content_analysis["recommendation"],
                "platforms": content_analysis.get("top_performers", []),
                "priority": "medium"
            })
        
        return learnings
    
    # ============ 保存学习结果 ============
    def save_learnings(self, learnings: list):
        """保存学习结果"""
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "learnings": learnings,
            "app_analysis": self.analyze_applications(),
            "salary_analysis": self.analyze_salary_trends(),
            "content_analysis": self.analyze_content_performance(),
        }
        
        # 保存最新
        path = FEEDBACK_DIR / "learnings.json"
        with open(path, "w") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # 追加历史
        hist_path = FEEDBACK_DIR / "learnings_history.json"
        history = []
        if hist_path.exists():
            with open(hist_path) as f:
                history = json.load(f)
        history.append({"timestamp": datetime.now().isoformat(), "learnings": learnings})
        # 只保留最近30条
        history = history[-30:]
        with open(hist_path, "w") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
        
        return path
    
    # ============ 主程序 ============
    def run(self):
        """运行学习流程"""
        print("🧠 Feedback Learner 启动...")
        print(f"   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # 生成学习
        learnings = self.generate_learnings()
        
        # 显示结果
        print(f"📊 生成 {len(learnings)} 条学习结果:\n")
        
        for i, l in enumerate(learnings, 1):
            icon = "🔴" if l["priority"] == "high" else "🟡"
            print(f"  {icon} [{l['type']}]")
            print(f"     {l['action']}")
            
            if l["type"] == "task_strategy":
                print(f"     平台: {l['platform']} | 置信度: {l.get('confidence',0)*100:.0f}%")
            print()
        
        # 保存
        path = self.save_learnings(learnings)
        print(f"💾 学习结果已保存: {path}")
        
        # 统计
        high = len([l for l in learnings if l["priority"] == "high"])
        medium = len([l for l in learnings if l["priority"] == "medium"])
        
        print(f"\n✅ 完成 | 高优: {high} | 中优: {medium}")
        
        return learnings

if __name__ == "__main__":
    learner = FeedbackLearner()
    learner.run()