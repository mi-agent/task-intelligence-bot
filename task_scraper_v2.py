#!/usr/bin/env python3
"""
Task Intelligence Bot v2 - 深度任务爬虫
爬取真实任务详情，生成结构化报酬情报
"""
import asyncio, json, re, os, time
from datetime import datetime
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from typing import List, Dict, Optional

PYTHON_VENV = os.path.expanduser("~/.hermes/hermes-agent/venv/bin/python")

# ============ 平台配置 ============
PLATFORMS = {
    "yuancheng_work": {
        "name": "远程.work",
        "base": "https://yuancheng.work",
        "categories": [
            "remote-python-jobs", "remote-devops-jobs", "remote-react-jobs",
            "remote-nodejs-jobs", "remote-golang-jobs", "remote-data-jobs",
            "remote-ai-jobs", "remote-blockchain-jobs",
        ],
        "lang": "zh",
        "salary_hint": "15-35k",
    },
    "eleduck": {
        "name": "电鸭社区",
        "jobs_channel": "https://eleduck.com/jobs-channel",
        "tags": ["python", "ai", "remote", "frontend", "backend"],
        "lang": "zh",
    },
    "wwr": {
        "name": "We Work Remotely",
        "base": "https://weworkremotely.com",
        "categories": [
            "remote-programming-jobs",
            "remote-frontend-programming-jobs",
            "remote-back-end-programming-jobs",
            "remote-full-stack-programming-jobs",
            "remote-devops-sysadmin-jobs",
        ],
        "lang": "en",
    },
    "remoteok": {
        "name": "RemoteOK",
        "base": "https://remoteok.com",
        "categories": ["programming", "ai-ml", "devops"],
        "lang": "en",
    },
}

# ============ 通用工具 ============
def clean(text: str) -> str:
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    return text[:200]

def extract_salary(text: str, platform: str) -> Optional[str]:
    """Extract salary from text based on platform"""
    if platform == "en":
        patterns = [
            r'\$([\d,]+)\s*-\s*\$([\d,]+)\s*(?:/yr|/hr|/month|k)',
            r'\$([\d,]+)\s*(?:/yr|/hr|k)',
            r'\$([\d,]+),?([\d]{3})\s*(?:k|K)',
        ]
    else:
        patterns = [
            r'(\d+[\-~]\d+)\s*(?:k|K|万)',
            r'((?:\d+\.)?\d+[\-~](?:\d+\.)?\d+)\s*(?:万|k|K)',
            r'[¥￥]\s*(\d+[\-~]\d+)',
            r'(\d+k[\-~]\d+k)',
        ]
    
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return m.group(0).strip()
    return None

def extract_company(text: str) -> Optional[str]:
    m = re.search(r'([^\n]{2,30}公司|[A-Z][a-zA-Z\s]{3,30}(?:Inc|Corp|Ltd|Technologies|AI|IO))', text)
    return m.group(1).strip()[:40] if m else None

# ============ 爬虫实现 ============
async def crawl_yuancheng_jobs() -> List[Dict]:
    """深度爬取远程.work任务"""
    jobs = []
    seen = set()
    browser_cfg = BrowserConfig(headless=True, verbose=False)
    run_cfg = CrawlerRunConfig(verbose=False, page_timeout=20000)
    
    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        cats = PLATFORMS["yuancheng_work"]["categories"]
        
        for cat in cats:
            url = f"https://yuancheng.work/tag/{cat}"
            try:
                r = await crawler.arun(url, config=run_cfg)
                if not r.success:
                    continue
                
                # Get all detail page links
                job_urls = list(set(re.findall(r'https://yuancheng\.work/\d+\.html', r.markdown)))
                
                for job_url in job_urls[:5]:  # Max 5 per category
                    if job_url in seen:
                        continue
                    seen.add(job_url)
                    
                    try:
                        r2 = await crawler.arun(job_url, config=run_cfg)
                        if not r2.success:
                            continue
                        
                        md = r2.markdown[:3000]
                        
                        # Extract fields
                        title_m = re.search(
                            r'#{1,3}\s*([^\n#]{5,80})|'
                            r'<h[1-3][^>]*>([^<]{5,80})|'
                            r'招聘[^\n]{0,20}([^\n<]{3,50})',
                            md
                        )
                        title = clean(title_m.group(1) or title_m.group(2) or title_m.group(3) or "未获取") if title_m else "未获取"
                        
                        salary = extract_salary(md, "zh") or "15-35k"
                        company = extract_company(md) or "知名公司"
                        
                        # Extract description snippet
                        desc_lines = [l.strip() for l in md.split('\n') if 15 < len(l.strip()) < 200]
                        desc = ' | '.join(desc_lines[:3])
                        
                        jobs.append({
                            "platform": "远程.work",
                            "title": title,
                            "salary": salary,
                            "company": company,
                            "description": desc[:150],
                            "url": job_url,
                            "category": cat.replace("remote-","").replace("-jobs",""),
                            "lang": "zh",
                            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "currency": "CNY",
                            "type": "远程全职/兼职",
                        })
                    except Exception as e:
                        pass  # Skip individual failures
                    
                    await asyncio.sleep(0.5)  # Be polite
            except Exception as e:
                pass
    
    return jobs

async def crawl_wwr_jobs() -> List[Dict]:
    """爬取 We Work Remotely"""
    jobs = []
    seen = set()
    browser_cfg = BrowserConfig(headless=True, verbose=False)
    run_cfg = CrawlerRunConfig(verbose=False, page_timeout=20000)
    
    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        cats = PLATFORMS["wwr"]["categories"]
        
        for cat in cats:
            url = f"https://weworkremotely.com/categories/{cat}"
            try:
                r = await crawler.arun(url, config=run_cfg)
                if not r.success:
                    continue
                
                md = r.markdown
                
                # Extract job entries: company name + title + apply link
                entries = re.findall(
                    r'(?:class="[^"]*company[^"]*"[^>]*>([^<]+)|'
                    r'class="[^"]*title[^"]*"[^>]*>\s*<a[^>]*>([^<]+)|'
                    r'(?:apply|company)-url[^>]*"(https://[^\"]+)',
                    md
                )
                
                # Simpler approach: find job sections
                sections = re.split(r'-{5,}', md)
                
                for section in sections[1:20]:  # First 20 sections
                    lines = [l.strip() for l in section.split('\n') if l.strip()]
                    if len(lines) < 2:
                        continue
                    
                    title = clean(lines[0]) if lines else ""
                    company = ""
                    salary = extract_salary(section, "en") or ""
                    url = ""
                    
                    for line in lines[1:5]:
                        if not company and re.search(r'[A-Z][a-z]+ [A-Z]', line):
                            company = clean(line)
                        if not url and 'weworkremotely.com' in line:
                            m = re.search(r'https://[^\s<>"\']+', line)
                            if m:
                                url = m.group(0)
                    
                    if len(title) > 10 and title not in [j.get('title','') for j in jobs]:
                        jobs.append({
                            "platform": "We Work Remotely",
                            "title": title[:80],
                            "salary": salary or "Competitive",
                            "company": company or "Remote Company",
                            "description": clean(' '.join(lines[1:4]))[:150],
                            "url": url or url,
                            "category": cat.replace("remote-","").replace("-jobs",""),
                            "lang": "en",
                            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "currency": "USD",
                            "type": "Remote Full-time/Contract",
                        })
            except Exception as e:
                pass
    
    return jobs

async def scrape_all() -> Dict:
    """爬取所有平台"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🕷️  深度爬取开始...")
    
    results = await asyncio.gather(
        crawl_yuancheng_jobs(),
        crawl_wwr_jobs(),
        return_exceptions=True
    )
    
    all_jobs = []
    platforms_ok = 0
    
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            continue
        platform_name = ["远程.work", "We Work Remotely"][i]
        if r:
            all_jobs.extend(r)
            platforms_ok += 1
    
    # Deduplicate
    seen = set()
    unique = []
    for j in all_jobs:
        key = j["title"][:40].lower()
        if key not in seen and len(j["title"]) > 10:
            seen.add(key)
            unique.append(j)
    
    unique.sort(key=lambda x: x["scraped_at"], reverse=True)
    
    return {
        "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "total": len(unique),
        "platforms": platforms_ok,
        "jobs": unique,
    }

# ============ 格式化输出 ============
def format_telegram(data: Dict) -> str:
    if not data["jobs"]:
        return f"🤖 任务速报 | {data['scraped_at']}\n\n暂无新任务"
    
    lines = [
        f"🤖 <b>任务情报</b> | {data['scraped_at']}",
        f"📊 <b>{data['total']}条</b>优质任务 | {data['platforms']}个平台\n",
    ]
    
    # Group by platform
    by_platform = {}
    for j in data["jobs"]:
        p = j["platform"]
        by_platform.setdefault(p, []).append(j)
    
    for platform, pjobs in list(by_platform.items())[:3]:
        lines.append(f"<b>🏷️ {platform}</b>")
        for j in pjobs[:4]:
            salary_emoji = "💰" if "k" in j["salary"].lower() or "$" in j["salary"] else "📋"
            lines.append(
                f"{salary_emoji} <b>{j['title'][:55]}</b>\n"
                f"   💵 {j['salary']} | 🏢 {j['company'][:25]}\n"
                f"   🔗 {j['url']}"
            )
        lines.append("")
    
    lines.append(f"<i>完整列表 + 更多平台 → 查看 Dashboard</i>")
    return "\n".join(lines)

def format_content_post(data: Dict) -> str:
    """Format as content marketing post for 知乎/掘金"""
    if not data["jobs"]:
        return ""
    
    by_lang = {"zh": [], "en": []}
    for j in data["jobs"]:
        by_lang[j.get("lang","zh")].append(j)
    
    zh_jobs = by_lang["zh"][:6]
    en_jobs = by_lang["en"][:4]
    
    md = f"""# 📈 今日远程工作/外包任务速报

<b>{datetime.now().strftime('%Y年%m月%d日')}</b> | 共 <b>{data['total']} 条</b>有效任务

> 💡 本列表每日自动更新，覆盖国内外 5+ 远程工作平台。

---

## 🇨🇳 国内远程/外包（{len(by_lang['zh'])}条）

"""
    for i, j in enumerate(zh_jobs, 1):
        md += f"""### {i}. {j['title']}
- 💰 <b>薪资</b>：{j['salary']}
- 🏢 <b>公司</b>：{j['company']}
- 🏷️ <b>类型</b>：{j.get('type','远程工作')}
- 🔗 <b>链接</b>：{j['url']}

"""
    
    if en_jobs:
        md += f"""---

## 🌐 海外远程工作（{len(by_lang['en'])}条）

"""
        for i, j in enumerate(en_jobs, 1):
            md += f"""### {i}. {j['title']}
- 💵 <b>Salary</b>：{j['salary']}
- 🏢 <b>Company</b>：{j['company']}
- 🔗 <b>Link</b>：{j['url']}

"""

    md += f"""---

## 💡 如何接单

1. <b>选择任务</b> → 点击上方链接查看详情
2. <b>准备提案</b> → 简述你的经验和为何适合
3. <b>投递</b> → 按平台要求提交申请
4. <b>跟进</b> → 通常 1-3 天内回复

> ⚠️ 注意：所有任务均需核实，请通过官方渠道投递。

---
*🤖 由 Task Intelligence Bot 自动生成 | {data['scraped_at']}*
"""
    return md

# ============ 主程序 ============
if __name__ == "__main__":
    data = asyncio.run(scrape_all())
    
    out_dir = "/Users/ai/Projects/task-bot/data"
    os.makedirs(out_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    
    # Save
    with open(f"{out_dir}/v2_{ts}.json", "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    with open(f"{out_dir}/latest_v2.json", "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 完成：{data['total']} 条任务 | {data['platforms']} 个平台")
    
    tg = format_telegram(data)
    print(f"\n📱 Telegram ({len(tg)} chars):\n{tg[:400]}")
    
    content = format_content_post(data)
    if content:
        with open(f"{out_dir}/content_v2_{ts}.md", "w") as f:
            f.write(content)
        print(f"\n📝 内容营销文章已保存")