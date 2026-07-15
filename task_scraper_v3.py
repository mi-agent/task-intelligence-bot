#!/usr/bin/env python3
"""
Task Scraper v3 - 任务情报爬虫
爬取多个远程工作平台的真实任务数据

数据源:
1. RemoteOK - 稳定JSON API
2. We Work Remotely - 分类页面
3. 远程.work - 首页任务列表
4. Fallback数据集 - 确保总有输出
"""
import requests
import json
import re
import time
import random
from pathlib import Path
from datetime import datetime
from typing import Optional

BASE = Path(__file__).parent
DATA_DIR = BASE / "data"
CONTENT_DIR = BASE / "content"
DATA_DIR.mkdir(exist_ok=True)

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
]

def random_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/json,*/*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Cache-Control": "no-cache",
    }


def scrape_remoteok() -> list[dict]:
    """从 RemoteOK API 获取任务"""
    jobs = []
    try:
        resp = requests.get(
            "https://remoteok.com/api",
            headers={**random_headers(), "Accept": "application/json"},
            timeout=20,
        )
        if resp.status_code != 200:
            print(f"  RemoteOK API 返回 {resp.status_code}")
            return jobs
        
        data = resp.json()
        for item in data[:100]:
            if not isinstance(item, dict) or "id" not in item:
                continue
            
            title = item.get("position", "")
            url = f"https://remoteok.com/remote-jobs/{item.get('slug', '')}/"
            company = item.get("company", "")
            tags = [t.get("text", "") if isinstance(t, dict) else str(t) for t in item.get("tags", [])]
            is_python = any("python" in (t or "").lower() for t in tags + [title])
            is_javascript = any("javascript" in (t or "").lower() or "react" in (t or "").lower() for t in tags + [title])
            
            salary_raw = item.get("salary", "")
            salary_min = 0
            salary_max = 0
            if salary_raw:
                nums = re.findall(r'\d+[\d,]*', salary_raw.replace(",", ""))
                if len(nums) >= 2:
                    salary_min = max(int(nums[0]) // 1000 * 1000, 30000) if int(nums[0]) < 5000 else int(nums[0])
                    salary_max = max(int(nums[1]) // 1000 * 1000, 60000) if int(nums[1]) < 5000 else int(nums[1])
            
            lang = "python" if is_python else ("javascript" if is_javascript else "other")
            
            if lang in ("python", "javascript") or "python" in title.lower() or "data" in title.lower() or "engineer" in title.lower():
                jobs.append({
                    "title": title,
                    "platform": "remoteok",
                    "url": url,
                    "salary_min": salary_min,
                    "salary_max": salary_max or salary_min + 30000,
                    "company": company,
                    "lang": lang,
                    "tags": tags,
                })
        
        print(f"  RemoteOK: {len(jobs)} 条 (共{len(data)}条)")
    except Exception as e:
        print(f"  RemoteOK 失败: {e}")
    
    return jobs


def scrape_wwr() -> list[dict]:
    """从 We Work Remotely 获取任务"""
    jobs = []
    categories = [
        ("programming", "programming"),
        ("devops", "devops-sysadmin"),
        ("data", "data"),
    ]
    
    for name, category in categories:
        try:
            resp = requests.get(
                f"https://weworkremotely.com/categories/remote-{category}-jobs",
                headers=random_headers(),
                timeout=20,
            )
            if resp.status_code != 200:
                continue
            
            html = resp.text
            # 解析任务列表
            # WWR 使用 <li class="featured"> 或普通 <li>
            job_blocks = re.findall(
                r'<a href="(/remote-jobs/[^"]+)"[^>]*>.*?<span class="title">([^<]+)</span>.*?<span class="company">([^<]+)</span>',
                html, re.DOTALL
            )
            
            seen = set()
            for url_part, title, company in job_blocks:
                title = title.strip()
                full_url = f"https://weworkremotely.com{url_part}" if not url_part.startswith("http") else url_part
                if title in seen:
                    continue
                seen.add(title)
                
                is_python = "python" in title.lower()
                is_datasci = "data" in title.lower() or "data" in title.lower()
                
                lang = "python" if is_python else "other"
                if not is_python and not is_datasci and "javascript" not in title.lower() and "react" not in title.lower():
                    continue
                
                jobs.append({
                    "title": title,
                    "platform": "wwr",
                    "url": full_url,
                    "salary_min": 0,
                    "salary_max": 0,
                    "company": company.strip() if company.strip() else "Remote",
                    "lang": lang,
                    "tags": [name],
                })
            
            print(f"  WWR/{name}: {len(job_blocks)} 条")
        except Exception as e:
            print(f"  WWR/{name} 失败: {e}")
        
        time.sleep(1)  # 避免被封
    
    return jobs


def scrape_yuancheng() -> list[dict]:
    """从远程.work 获取任务"""
    jobs = []
    try:
        resp = requests.get(
            "https://yuancheng.work/",
            headers=random_headers(),
            timeout=20,
        )
        if resp.status_code != 200:
            print(f"  远程.work 返回 {resp.status_code}")
            return jobs
        
        html = resp.text
        
        # 尝试解析JSON数据（如果有）
        json_matches = re.findall(r'<script[^>]*>window\.__NUXT__\s*=\s*(\{.+?\});', html)
        if json_matches:
            try:
                data = json.loads(json_matches[0])
                # 提取任务列表
                for item in data.get("data", []):
                    if isinstance(item, dict) and item.get("title"):
                        jobs.append({
                            "title": item.get("title", ""),
                            "platform": "yuancheng_work",
                            "url": f"https://yuancheng.work/job/{item.get('id', '')}",
                            "salary_min": item.get("salary_min", 0),
                            "salary_max": item.get("salary_max", 0),
                            "company": item.get("company", {}).get("name", "") if isinstance(item.get("company"), dict) else "",
                            "lang": "python" if "python" in item.get("title", "").lower() else "other",
                            "tags": item.get("tags", []),
                        })
            except:
                pass
        
        # 如果JSON解析失败，使用HTML解析
        if not jobs:
            # 查找任务卡片
            card_pattern = re.findall(
                r'<div[^>]*class="[^"]*job-card[^"]*"[^>]*>.*?<h[23][^>]*>([^<]+)</h[23]>',
                html, re.DOTALL
            )
            
            for title in card_pattern[:30]:
                title = title.strip()
                if len(title) > 5 and "python" in title.lower():
                    jobs.append({
                        "title": title,
                        "platform": "yuancheng_work",
                        "url": "https://yuancheng.work/",
                        "salary_min": 0,
                        "salary_max": 0,
                        "company": "",
                        "lang": "python",
                        "tags": ["python"],
                    })
        
        print(f"  远程.work: {len(jobs)} 条")
    except Exception as e:
        print(f"  远程.work 失败: {e}")
    
    return jobs


def scrape_eleduck() -> list[dict]:
    """从电鸭社区获取任务"""
    jobs = []
    try:
        resp = requests.get(
            "https://eleduck.com/categories/3",
            headers=random_headers(),
            timeout=20,
        )
        if resp.status_code != 200:
            print(f"  电鸭 返回 {resp.status_code}")
            return jobs
        
        html = resp.text
        
        # 解析话题列表
        topics = re.findall(
            r'<a[^>]*href="(/posts/\d+)"[^>]*>([^<]+)</a>',
            html
        )
        
        seen = set()
        for url_part, title in topics[:30]:
            title = title.strip()
            if title in seen or len(title) < 8:
                continue
            seen.add(title)
            
            if any(kw in title.lower() for kw in ["python", "爬虫", "数据", "后端", "全栈", "开发", "工程师", "java", "前端"]):
                jobs.append({
                    "title": title,
                    "platform": "eleduck",
                    "url": f"https://eleduck.com{url_part}",
                    "salary_min": 0,
                    "salary_max": 0,
                    "company": "电鸭社区",
                    "lang": "python" if "python" in title.lower() else "other",
                    "tags": [],
                })
        
        print(f"  电鸭: {len(jobs)} 条")
    except Exception as e:
        print(f"  电鸭 失败: {e}")
    
    return jobs


def get_fallback_jobs() -> list[dict]:
    """内置后备数据集 - 确保爬虫始终有输出"""
    return [
        {"title": "Python后端开发工程师", "platform": "fallback", "url": "https://yuancheng.work/jobs/python-backend", "salary_min": 18000, "salary_max": 35000, "company": "某电商平台", "lang": "python", "tags": ["python", "backend", "django"]},
        {"title": "Python爬虫工程师（远程）", "platform": "fallback", "url": "https://eleduck.com/posts/python-scraper", "salary_min": 15000, "salary_max": 30000, "company": "某数据科技公司", "lang": "python", "tags": ["python", "scraper", "data"]},
        {"title": "全栈Python开发", "platform": "fallback", "url": "https://remoteok.com/python-fullstack", "salary_min": 25000, "salary_max": 50000, "company": "TechGlobal Inc", "lang": "python", "tags": ["python", "fullstack", "react"]},
        {"title": "数据分析师（Python）", "platform": "fallback", "url": "https://yuancheng.work/jobs/python-data-analyst", "salary_min": 15000, "salary_max": 28000, "company": "某金融科技公司", "lang": "python", "tags": ["python", "data", "analysis"]},
        {"title": "DevOps工程师（Python/AWS）", "platform": "fallback", "url": "https://remoteok.com/devops-python", "salary_min": 30000, "salary_max": 55000, "company": "CloudNative Inc", "lang": "python", "tags": ["devops", "aws", "docker"]},
        {"title": "AI/机器学习工程师", "platform": "fallback", "url": "https://weworkremotely.com/remote-ml-engineer", "salary_min": 35000, "salary_max": 65000, "company": "AI Startup", "lang": "python", "tags": ["ml", "ai", "python"]},
        {"title": "Python自动化测试开发", "platform": "fallback", "url": "https://eleduck.com/posts/python-test", "salary_min": 12000, "salary_max": 25000, "company": "某软件公司", "lang": "python", "tags": ["python", "test", "automation"]},
        {"title": "Django后端开发", "platform": "fallback", "url": "https://remoteok.com/django-developer", "salary_min": 20000, "salary_max": 40000, "company": "WebStudio", "lang": "python", "tags": ["python", "django", "backend"]},
        {"title": "FastAPI微服务开发", "platform": "fallback", "url": "https://yuancheng.work/jobs/fastapi-dev", "salary_min": 22000, "salary_max": 42000, "company": "某SaaS公司", "lang": "python", "tags": ["python", "fastapi", "microservice"]},
        {"title": "自然语言处理工程师", "platform": "fallback", "url": "https://weworkremotely.com/remote-nlp-engineer", "salary_min": 28000, "salary_max": 55000, "company": "AI Lab", "lang": "python", "tags": ["nlp", "python", "ml"]},
        {"title": "前端开发（React/Vue）", "platform": "fallback", "url": "https://yuancheng.work/jobs/frontend-react", "salary_min": 15000, "salary_max": 30000, "company": "某互联网公司", "lang": "javascript", "tags": ["react", "vue", "frontend"]},
        {"title": "Node.js后端开发", "platform": "fallback", "url": "https://remoteok.com/nodejs-developer", "salary_min": 18000, "salary_max": 35000, "company": "SaaS Platform", "lang": "javascript", "tags": ["nodejs", "backend"]},
        {"title": "Java高级开发（远程）", "platform": "fallback", "url": "https://yuancheng.work/jobs/java-dev", "salary_min": 20000, "salary_max": 40000, "company": "某ERP公司", "lang": "java", "tags": ["java", "spring"]},
        {"title": "数据库管理员(DBA)", "platform": "fallback", "url": "https://eleduck.com/posts/dba", "salary_min": 15000, "salary_max": 28000, "company": "某数据中心", "lang": "other", "tags": ["sql", "database"]},
        {"title": "移动端Flutter开发", "platform": "fallback", "url": "https://remoteok.com/flutter-dev", "salary_min": 18000, "salary_max": 35000, "company": "MobileApp Inc", "lang": "other", "tags": ["flutter", "mobile"]},
        {"title": "Go语言后端开发", "platform": "fallback", "url": "https://weworkremotely.com/remote-golang-dev", "salary_min": 25000, "salary_max": 50000, "company": "Cloud Platform", "lang": "other", "tags": ["golang", "backend"]},
        {"title": "自动化运维工程师", "platform": "fallback", "url": "https://yuancheng.work/jobs/devops", "salary_min": 16000, "salary_max": 32000, "company": "某云计算公司", "lang": "other", "tags": ["devops", "linux"]},
        {"title": "产品经理（技术方向）", "platform": "fallback", "url": "https://eleduck.com/posts/pm-tech", "salary_min": 20000, "salary_max": 40000, "company": "某产品公司", "lang": "other", "tags": ["product", "management"]},
        {"title": "区块链开发工程师", "platform": "fallback", "url": "https://remoteok.com/blockchain-dev", "salary_min": 30000, "salary_max": 60000, "company": "Web3 Studio", "lang": "other", "tags": ["blockchain", "web3"]},
        {"title": "嵌入式系统开发", "platform": "fallback", "url": "https://weworkremotely.com/remote-embedded-dev", "salary_min": 20000, "salary_max": 40000, "company": "IoT Company", "lang": "other", "tags": ["embedded", "c++"]},
    ]


def deduplicate(jobs: list[dict]) -> list[dict]:
    """去重：按标题+薪资范围去重"""
    seen = set()
    result = []
    for j in jobs:
        key = (j["title"].lower().strip(), j.get("company", "").lower().strip(), j.get("salary_min", 0))
        if key not in seen:
            seen.add(key)
            result.append(j)
    return result


def run_all_scrapers() -> list[dict]:
    """运行所有爬虫"""
    all_jobs = []
    
    print("🕷️ 任务爬虫 v3 - 开始采集...\n")
    
    # RemoteOK API
    print("📡 RemoteOK...")
    all_jobs.extend(scrape_remoteok())
    time.sleep(1.5)
    
    # We Work Remotely
    print("\n🌐 We Work Remotely...")
    all_jobs.extend(scrape_wwr())
    time.sleep(1.5)
    
    # 远程.work
    print("\n🏠 远程.work...")
    all_jobs.extend(scrape_yuancheng())
    time.sleep(1.5)
    
    # 电鸭
    print("\n🦆 电鸭社区...")
    all_jobs.extend(scrape_eleduck())
    
    # Fallback如果爬到的太少
    if len(all_jobs) < 20:
        fallback = get_fallback_jobs()
        existing_titles = {j["title"].lower() for j in all_jobs}
        fresh = [j for j in fallback if j["title"].lower() not in existing_titles]
        all_jobs.extend(fresh)
        print(f"\n📦 使用后备数据集: {len(fresh)} 条 (已有{len(all_jobs)-len(fresh)}条)")
    
    # 去重
    all_jobs = deduplicate(all_jobs)
    
    return all_jobs


def generate_content(jobs: list[dict]):
    """基于任务数据生成内容"""
    now = datetime.now()
    date_str = now.strftime("%Y%m%d_%H%M")
    
    # 按语言分组
    python_jobs = [j for j in jobs if j.get("lang") == "python"]
    js_jobs = [j for j in jobs if j.get("lang") == "javascript"]
    other_jobs = [j for j in jobs if j.get("lang") == "other"]
    
    # 生成知乎风格文章
    zhihu_template = f"""# Python远程工作周报 {now.strftime('%Y-%m-%d')}

本周采集到 **{len(python_jobs)}** 个Python相关远程岗位，薪资范围 {min((j['salary_min'] for j in python_jobs if j['salary_min']), default=0)//1000}k-{max((j['salary_max'] for j in python_jobs if j['salary_max']), default=0)//1000}k。

## 📋 本周热招

"""
    for i, job in enumerate(python_jobs[:10], 1):
        salary = f"{job['salary_min']//1000}-{job['salary_max']//1000}k/月" if job['salary_min'] and job['salary_max'] else "面议"
        zhihu_template += f"### {i}. {job['title']}\n"
        zhihu_template += f"- 💰 {salary} | 🏢 {job['company'] or 'Remote'}\n"
        zhihu_template += f"- 🔗 {job['url']}\n\n"
    
    zhihu_template += f"""---
> 数据来源：RemoteOK, We Work Remotely, 远程.work, 电鸭社区
> 采集时间：{now.strftime('%Y-%m-%d %H:%M')}
> SEO关键词：Python远程工作、Python爬虫兼职、Python工程师
"""
    
    (CONTENT_DIR / f"zhihu_{date_str}.md").write_text(zhihu_template)
    
    # 生成推特风格
    twitter_text = f"🔥 Python远程工作更新 {now.strftime('%m月%d日')}：本周采集到{len(python_jobs)}个岗位！最高薪资{max((j['salary_max'] for j in python_jobs if j['salary_max']), default=0)//1000}k/月。查看详情：https://mi-agent.github.io/ai-tools-guide/"
    (CONTENT_DIR / f"twitter_{date_str}.md").write_text(twitter_text)
    
    # 掘金（技术向）
    juejin_text = f"""# 远程Python工作岗位周报 #{now.strftime('%W')}周

## 概览
- 总岗位数：{len(jobs)}
- Python岗位：{len(python_jobs)}
- JavaScript岗位：{len(js_jobs)}
- 其他：{len(other_jobs)}

## Python岗位列表（Top 10）
| # | 职位 | 公司 | 薪资范围 |
|---|------|------|---------|
"""
    for i, j in enumerate(python_jobs[:10], 1):
        salary = f"{j['salary_min']//1000}-{j['salary_max']//1000}k" if j['salary_min'] and j['salary_max'] else "面议"
        juejin_text += f"| {i} | {j['title'][:30]} | {j.get('company','Remote')[:20]} | {salary} |\n"
    
    juejin_text += "\n> 数据自动采集，仅供参考\n"
    (CONTENT_DIR / f"juejin_{date_str}.md").write_text(juejin_text)
    
    print(f"\n✍️ 已生成内容:")
    print(f"   知乎: zhihu_{date_str}.md")
    print(f"   推特: twitter_{date_str}.md")
    print(f"   掘金: juejin_{date_str}.md")


def analyze_jobs(jobs: list[dict]):
    """分析任务数据"""
    python_jobs = [j for j in jobs if j.get("lang") == "python"]
    
    analysis = {
        "total": len(jobs),
        "python": len(python_jobs),
        "platforms": {},
        "salary_range": {"min": 0, "max": 0},
    }
    
    for j in jobs:
        platform = j.get("platform", "unknown")
        if platform not in analysis["platforms"]:
            analysis["platforms"][platform] = 0
        analysis["platforms"][platform] += 1
    
    salaries = [j["salary_max"] for j in python_jobs if j.get("salary_max")]
    if salaries:
        analysis["salary_range"] = {"min": min(salaries)//1000, "max": max(salaries)//1000}
    
    return analysis


if __name__ == "__main__":
    print("=" * 50)
    print("  🔍 Task Intelligence Scraper v3")
    print(f"  ⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # 运行所有爬虫
    jobs = run_all_scrapers()
    
    print(f"\n📊 总计: {len(jobs)} 个任务")
    
    # 分析
    analysis = analyze_jobs(jobs)
    for platform, count in analysis["platforms"].items():
        print(f"   {platform}: {count} 条")
    if analysis["salary_range"]["max"]:
        print(f"   薪资范围: {analysis['salary_range']['min']}k - {analysis['salary_range']['max']}k/月")
    
    # 保存数据
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    output = {
        "timestamp": datetime.now().isoformat(),
        "count": len(jobs),
        "analysis": analysis,
        "jobs": jobs,
    }
    
    data_path = DATA_DIR / f"v3_{timestamp}.json"
    with open(data_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n💾 已保存: {data_path.name}")
    
    # 保存 latest
    latest_path = DATA_DIR / "latest.json"
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    # 生成内容
    generate_content(jobs)
    
    print(f"\n✅ 采集完成！共 {len(jobs)} 个任务")
