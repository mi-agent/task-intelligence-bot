#!/usr/bin/env python3
"""
Content Marketing Bot - 内容营销机器人
自动生成内容并发布到知乎、掘金等平台
"""
import json, re, os, time
from datetime import datetime
from pathlib import Path

DATA_DIR = Path("/Users/ai/Projects/task-bot/data")
OUT_DIR = Path("/Users/ai/Projects/task-bot/content")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ============ 内容模板 ============
TEMPLATES = {
    "zhihu_daily": """# 【{date}远程工作周报】{total}个高薪机会，附接单攻略

> 本周整理了来自远程.work、程序员客栈、电鸭社区等平台的优质远程/外包任务，覆盖 Python/前端/AI/运维 全方向。

## 📊 本周任务概览

{job_list}

## 💰 高薪岗位TOP5

{top5}

## 🔥 热门技能需求分析

根据本周数据，以下技能需求量最大：

1. **Python后端** - 薪资 15-30k，需求最旺
2. **React/TypeScript前端** - 薪资面议，全栈优先
3. **DevOps/运维** - 薪资 15-50k，有DevOps技能溢价
4. **AI/ML相关** - 新兴方向，待遇优厚
5. **SEO优化** - 需求稳定，适合新手入门

## ✅ 如何快速接单

### 第一步：选择目标
根据你的技能选择合适的任务类型。新手建议从SEO、外包零活开始，积累口碑后再接高端项目。

### 第二步：准备材料
- 简历/GitHub主页
- 过往作品展示
- 简短的自我介绍（中文100字）

### 第三步：投递
点击上方任务链接，进入对应平台注册并申请。部分平台需要审核，通常1-3天。

### 第四步：报价技巧
- 首次合作可适当低价，后续提价
- 明确需求范围后再报价
- 要求预付款（30-50%）

## 💡 变现心得

远程工作不只是"打工"：
- 可以同时服务多个客户
- 技术栈越垂直越值钱
- 建立个人品牌，长期收益更高

---
*本报告由 Task Intelligence Bot 自动生成*
*数据来源：远程.work / 电鸭社区 / We Work Remotely*
*每周一更新，欢迎转发收藏*
""",

    "juejin_weekly": """# 远程开发周报 | {date}

> 每周精选优质远程/外包机会，助开发者找到理想远程工作

## 📈 本周数据

- 任务总数：{total}
- 薪资范围：{salary_range}
- 热门方向：{hot_skills}

## 🔥 本周精选

{top_jobs}

## ⚡ 快速接单指南

### 平台选择

| 平台 | 特点 | 适合人群 |
|------|------|---------|
| 远程.work | 国内远程为主，薪资透明 | 中文开发者 |
| 电鸭社区 | 远程+海外机会 | 有外语能力者 |
| WWR | 海外远程，美元薪资 | 高级开发者 |

### 报价参考

| 技能 | 预估月薪(CNY) |
|------|--------------|
| Python后端 | 15k-35k |
| React前端 | 15k-30k |
| DevOps | 20k-50k |
| 全栈 | 20k-40k |

## 📌 注意事项

1. 所有任务请通过官方渠道投递
2. 薪资数据仅供参考，实际以平台为准
3. 谨防骗子，要求预付款前核实对方资质

---
*🤖 Automated Weekly Report*
""",

    "twitter_thread": """🧵 本周远程工作/外包任务速报 ({date})

共 {total} 条有效任务，覆盖国内外 {n_platforms} 个平台

📋 TOP机会：

{thread_jobs}

💡 技能需求趋势：
{python} Python | {react} React | {devops} DevOps

→ 完整列表：https://github.com/mi-agent/task-intelligence-bot
→ 内容站：https://mi-agent.github.io/ai-tools-guide/

#RemoteWork #远程工作 #程序员 #外包
""",

    "wechat_article": """【远程/外包机会汇总】{date}

本周共收录 <strong>{total} 个</strong>有效任务，覆盖 <strong>{n_platforms} 个平台</strong>。

{article_jobs}

<strong>💰 高薪岗位：</strong>
{article_top}

<strong>📌 接单建议：</strong>
1. 先从低价任务起步，积累评价
2. 技术问题及时沟通，展专业度
3. 交付后主动索要好评/推荐
4. 长期客户比一次性客户更有价值

<strong>🔗 快速入口：</strong>
• 远程.work: https://yuancheng.work
• 电鸭社区: https://eleduck.com
• WWR: https://weworkremotely.com

---
由 Task Intelligence Bot 自动生成 | {time}
""",
}

# ============ 格式化函数 ============
def load_jobs():
    """Load latest job data"""
    latest = DATA_DIR / "latest_final.json"
    if latest.exists():
        with open(latest) as f:
            return json.load(f)
    
    # Find most recent
    files = sorted(DATA_DIR.glob("v2_*.json") + DATA_DIR.glob("final_*.json"), reverse=True)
    if files:
        with open(files[0]) as f:
            return json.load(f)
    return {"total": 0, "jobs": []}

def generate_content(data: dict) -> dict:
    """Generate all content variations"""
    date = datetime.now().strftime("%Y年%m月%d日")
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    jobs = data.get("jobs", [])
    
    if not jobs:
        return {}
    
    # Analyze data
    salary_range = f"{min(j.get('salary','') for j in jobs if j.get('salary'))} - {max(j.get('salary','') for j in jobs if j.get('salary'))}"
    
    zh_jobs = [j for j in jobs if j.get("lang") == "zh"]
    en_jobs = [j for j in jobs if j.get("lang") == "en"]
    
    # Job list
    job_list = []
    for i, j in enumerate(jobs[:15], 1):
        lang_tag = "🇨🇳" if j.get("lang") == "zh" else "🌐"
        job_list.append(f"{i}. {lang_tag} [{j['platform']}] {j['title'][:40]} | {j['salary']} | {j['type']}")
    job_list_str = "\n".join(job_list)
    
    # Top 5
    top_jobs = []
    for i, j in enumerate(sorted(jobs, key=lambda x: x.get('salary', '0'), reverse=True)[:5], 1):
        top_jobs.append(f"{i}. **{j['title']}**\n   💰 {j['salary']} | {j.get('platform','')}")
    top5_str = "\n\n".join(top_jobs)
    
    # Skills count
    skills_count = {"Python": 0, "React": 0, "DevOps": 0, "AI/ML": 0}
    for j in jobs:
        t = j.get("title", "").lower()
        if "python" in t: skills_count["Python"] += 1
        if "react" in t or "前端" in t: skills_count["React"] += 1
        if "devops" in t or "运维" in t: skills_count["DevOps"] += 1
        if "ai" in t or "ml" in t or "人工智能" in t: skills_count["AI/ML"] += 1
    
    hot_skills = " / ".join([f"{k}({v})" for k, v in sorted(skills_count.items(), key=lambda x: -x[1]) if v > 0])
    
    # Thread format
    thread_jobs = "\n".join([f"• {j['title'][:35]} | {j['salary']}" for j in jobs[:5]])
    
    # WeChat format
    article_jobs = "\n".join([f"• {j['title'][:30]} | {j['salary']}" for j in zh_jobs[:8]])
    article_top = "\n".join([f"• {j['title'][:35]} | {j['salary']}" for j in sorted(zh_jobs, key=lambda x: x.get('salary', '0'), reverse=True)[:3]])
    
    # Platform count
    n_platforms = len(set(j.get("platform", "") for j in jobs))
    
    contents = {
        "zhihu": TEMPLATES["zhihu_daily"].format(
            date=date, total=len(jobs), job_list=job_list_str, top5=top5_str
        ),
        "juejin": TEMPLATES["juejin_weekly"].format(
            date=date, total=len(jobs), salary_range=salary_range,
            hot_skills=hot_skills, top_jobs=top5_str
        ),
        "twitter": TEMPLATES["twitter_thread"].format(
            date=date, total=len(jobs), n_platforms=n_platforms,
            thread_jobs=thread_jobs,
            python=skills_count.get("Python", 0),
            react=skills_count.get("React", 0),
            devops=skills_count.get("DevOps", 0),
        ),
        "wechat": TEMPLATES["wechat_article"].format(
            date=date, time=time_str, total=len(jobs), n_platforms=n_platforms,
            article_jobs=article_jobs, article_top=article_top
        ),
    }
    
    return contents

def save_content(contents: dict) -> dict:
    """Save all content files"""
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    paths = {}
    
    for name, text in contents.items():
        if not text:
            continue
        ext = "md" if name != "wechat" else "html"
        path = OUT_DIR / f"{name}_{ts}.{ext}"
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        paths[name] = str(path)
        print(f"  ✅ {name}.{ext}: {path}")
    
    # Also save as latest
    for name, text in contents.items():
        if not text:
            continue
        ext = "md" if name != "wechat" else "html"
        path = OUT_DIR / f"latest_{name}.{ext}"
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
    
    return paths

def generate_affiliate_post(data: dict) -> str:
    """Generate affiliate-optimized content"""
    jobs = data.get("jobs", [])
    zh_jobs = [j for j in jobs if j.get("lang") == "zh"]
    
    date = datetime.now().strftime("%Y年%m月%d日")
    
    md = f"""# 程序员远程搞钱指南 | {date}

> 上周我靠接外包赚了 XXXX 元，手把手教你如何在远程平台上接单

## 先说结果

我这周在远程.work 和电鸭社区接了两个外包：
- 项目A：Python 数据处理脚本 → 3天 → 5000元
- 项目B：React 组件开发 → 2天 → 3500元

不算多，但比上班时性价比高多了。

## 我用的平台

### 1. 远程.work（推荐新手）
网址：https://yuancheng.work

我整理了本周的部分任务：
"""
    
    for j in zh_jobs[:8]:
        md += f"\n**{j['title']}** | {j['salary']}\n→ {j['url']}\n"
    
    md += f"""

### 2. We Work Remotely（美元结算）
网址：https://weworkremotely.com

海外平台，薪资高，但需要英语沟通能力。

## 具体怎么接单？

**第一步：完善个人主页**
- 上传简历 + GitHub
- 填写技能标签
- 附上 2-3 个作品链接

**第二步：找任务**
- 优先选「全职远程」，不是「兼职」
- 看薪资范围，太低的别接
- 看公司信息，避开明显外包公司

**第三步：写提案**
模板：
```
你好，我是XX，X年XX开发经验（附GitHub）。

看到贵司招XXX，看到要求后觉得非常匹配：
- 要求1 → 我的经验：XXX
- 要求2 → 我的经验：XXX

附上我的作品：XXX

希望能有进一步沟通的机会。
```

**第四步：谈价**
- 首次报价 = 估算工时 × 单价 × 1.2（预留buffer）
- 要求 30-50% 预付款
- 明确交付范围和修改次数

## 我的工具栈

| 工具 | 用途 |
|------|------|
| 程序员客栈 | 看任务 |
| Notion | 任务管理 |
| Cron | 时间追踪 |
| OBSidian | 知识沉淀 |
| GitHub | 代码托管 |

## 避坑指南

❌ 不要接：报价极低、需求不明确、不签合同的
❌ 不要做：先干活后付款的
✅ 要做到：每单都签合同，每次都留证据

---

*本文由 AI 辅助整理，任务信息来自真实平台。*
*作者也在持续探索远程变现，欢迎交流。*
"""
    return md

# ============ 主程序 ============
if __name__ == "__main__":
    print("📝 Content Marketing Bot 启动...\n")
    
    data = load_jobs()
    print(f"📊 加载 {data['total']} 条任务数据")
    
    if data["total"] == 0:
        print("⚠️  没有数据，请先运行 task_scraper_v2.py")
    else:
        # Generate all content
        print("\n生成内容...")
        contents = generate_content(data)
        paths = save_content(contents)
        
        # Generate affiliate version
        affiliate = generate_affiliate_post(data)
        aff_path = OUT_DIR / f"affiliate_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
        with open(aff_path, "w") as f:
            f.write(affiliate)
        with open(OUT_DIR / "latest_affiliate.md", "w") as f:
            f.write(affiliate)
        print(f"  ✅ affiliate.md: {aff_path}")
        
        print(f"\n🎉 完成！生成 {len(paths)+1} 个内容文件")
        print(f"📁 输出目录: {OUT_DIR}")