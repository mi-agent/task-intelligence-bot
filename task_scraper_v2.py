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
    "zbj": {
        "name": "猪八戒",
        "base": "https://task.zbj.com",
        "categories": [
            "rjgw",  # 软件开发
            "wxkf",  # 网站建设
            "appkf", # APP开发
            "sjkfw", # 数据服务
        ],
        "lang": "zh",
        "salary_hint": "500-5000/单",
    },
    "ipweike": {
        "name": "一品威客",
        "base": "https://www.epwk.com",
        "categories": [
            "software",      # 软件开发
            "website",       # 网站建设
            "mobile-app",    # APP开发
            "design",        # 设计服务
        ],
        "lang": "zh",
        "salary_hint": "1000-10000/单",
    },
}

# ============ 通用工具 ============
def clean(text: str) -> str:
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    return text[:200]

def standardize_salary(salary: str, lang: str = "zh") -> dict:
    """
    标准化薪资数据，返回统一格式的字典
    返回格式: {"raw": str, "min": float, "max": float, "unit": str, "currency": str, "display": str}
    """
    result = {"raw": salary, "min": 0, "max": 0, "unit": "", "currency": "CNY", "display": salary}
    
    if not salary:
        return result
    
    # 中文薪资处理
    if lang == "zh":
        # 处理 "15-35k" 或 "15K-35K" 格式
        m = re.search(r'(\d+(?:\.\d+)?)\s*[kK万]?\s*[-~至到]\s*(\d+(?:\.\d+)?)\s*[kK万]?', salary)
        if m:
            min_val, max_val = float(m.group(1)), float(m.group(2))
            unit_match = re.search(r'([kK万])', salary)
            unit = unit_match.group(1) if unit_match else "k"
            
            if unit == "万":
                result["min"] = min_val * 10  # 转换为k
                result["max"] = max_val * 10
                result["currency"] = "CNY"
                result["display"] = f"{min_val}-{max_val}万/年"
            else:
                result["min"] = min_val
                result["max"] = max_val
                result["currency"] = "CNY"
                result["display"] = f"{min_val}-{max_val}k/月"
            return result
        
        # 单值处理 "20k" 或 "2万"
        m = re.search(r'(\d+(?:\.\d+)?)\s*([kK万])', salary)
        if m:
            val = float(m.group(1))
            unit = m.group(2)
            if unit == "万":
                result["min"] = result["max"] = val * 10
                result["display"] = f"约{val}万/年"
            else:
                result["min"] = result["max"] = val
                result["display"] = f"约{val}k/月"
            return result
            
        # 处理元格式 "5000-10000元/月"
        m = re.search(r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*[-~至到]\s*(\d+(?:,\d{3})*(?:\.\d+)?)', salary.replace(',', ''))
        if m:
            min_val, max_val = float(m.group(1)), float(m.group(2))
            if min_val > 1000:  # 超过1000的按月薪算
                result["min"] = min_val / 1000
                result["max"] = max_val / 1000
                result["display"] = f"{min_val/1000:.0f}-{max_val/1000:.0f}k/月"
            else:
                result["min"] = result["max"] = min_val
                result["display"] = f"{min_val}k/月"
            return result
    
    # 英文薪资处理 (USD)
    if lang == "en":
        # 时薪格式 $50-100/hr
        m = re.search(r'\$(\d+(?:,\d{3})*(?:\.\d+)?)\s*[-~至到]\s*\$?(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:/hr|per hour|hourly)', salary, re.I)
        if m:
            result["min"] = float(m.group(1).replace(',', ''))
            result["max"] = float(m.group(2).replace(',', ''))
            result["unit"] = "hr"
            result["currency"] = "USD"
            # 转换为年薪估算 (40h/week * 52周)
            result["display"] = f"${result['min']}-${result['max']}/hr (≈${result['min']*2080/1000:.0f}k-${result['max']*2080/1000:.0f}k/年)"
            return result
        
        # 年薪格式 $80k-150k 或 $80,000-$150,000
        m = re.search(r'\$(\d+(?:,\d{3})*(?:\.\d+)?)\s*[-~至到]\s*\$?(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:k|K|/yr|per year|yearly)?', salary, re.I)
        if m:
            val1 = float(m.group(1).replace(',', ''))
            val2 = float(m.group(2).replace(',', ''))
            # 如果数值大于1000且有k或/yr，认为是年薪
            if 'k' in salary.lower() or '/yr' in salary.lower() or (val1 > 1000 and val2 > 1000):
                result["min"] = val1 / 1000 if val1 > 100 else val1
                result["max"] = val2 / 1000 if val2 > 100 else val2
            else:
                result["min"] = val1
                result["max"] = val2
            result["unit"] = "yr"
            result["currency"] = "USD"
            result["display"] = f"${result['min']}k-${result['max']}k/年"
            return result
        
        # 月薪格式
        m = re.search(r'\$(\d+(?:,\d{3})*(?:\.\d+)?)\s*[-~至到]\s*\$?(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:/mo|per month|monthly)', salary, re.I)
        if m:
            result["min"] = float(m.group(1).replace(',', ''))
            result["max"] = float(m.group(2).replace(',', ''))
            result["unit"] = "mo"
            result["currency"] = "USD"
            result["display"] = f"${result['min']}-{result['max']}/月"
            return result
    
    # 猪八戒/一品威客 单次项目报价格式
    m = re.search(r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*[-~至到]\s*(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:元|块)', salary)
    if m:
        result["min"] = float(m.group(1).replace(',', ''))
        result["max"] = float(m.group(2).replace(',', ''))
        result["currency"] = "CNY"
        result["display"] = f"¥{result['min']:,.0f}-{result['max']:,.0f}/单"
        return result
    
    return result

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
            r'(\d+(?:,\d{3})*\s*[-~至到]\s*\d+(?:,\d{3})*)\s*(?:元|块)',  # 中文金额
            r'((?:\d+\.)?\d+万)',  # 万结尾
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
    """爬取 We Work Remotely - 改进版"""
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
                
                # 改进: 使用更精确的解析模式
                # 匹配格式: 公司名 + 职位 + 地点/公司类型 + 链接
                job_pattern = re.compile(
                    r'(?:^|\n)\s*([A-Z][A-Za-z\s&,\.]+(?:Inc|Corp|Ltd|LLC|Technologies|IO|AI|Co)?)\s*[-–—]\s*\n?\s*([^\n]+?(?:Remote|Full[- ]?Time|Part[- ]?Time|Contract)[^\n]*)\n?\s*(?:[^<\n]*公司)?\s*'
                    r'(https://weworkremotely\.com/jobs/\d+)',
                    re.MULTILINE | re.IGNORECASE
                )
                
                for match in job_pattern.finditer(md):
                    company = clean(match.group(1))
                    title = clean(match.group(2))
                    job_url = match.group(3)
                    
                    if job_url in seen or len(title) < 10:
                        continue
                    seen.add(job_url)
                    
                    # 获取该职位的详情片段
                    section_start = match.start()
                    section_end = min(section_start + 500, len(md))
                    section = md[section_start:section_end]
                    
                    salary = extract_salary(section, "en") or "Competitive"
                    
                    jobs.append({
                        "platform": "We Work Remotely",
                        "title": title[:80],
                        "salary": salary,
                        "company": company[:40],
                        "description": clean(' '.join(section.split('\n')[2:5]))[:150],
                        "url": job_url,
                        "category": cat.replace("remote-","").replace("-jobs",""),
                        "lang": "en",
                        "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "currency": "USD",
                        "type": "Remote Full-time/Contract",
                    })
                    
                    await asyncio.sleep(0.3)  # 礼貌延迟
                    
            except Exception as e:
                pass
    
    return jobs

async def crawl_zbj_tasks() -> List[Dict]:
    """爬取猪八戒任务"""
    jobs = []
    seen = set()
    browser_cfg = BrowserConfig(headless=True, verbose=False)
    run_cfg = CrawlerRunConfig(verbose=False, page_timeout=20000)
    
    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        cats = PLATFORMS["zbj"]["categories"]
        
        for cat in cats:
            url = f"https://task.zbj.com/{cat}/"
            try:
                r = await crawler.arun(url, config=run_cfg)
                if not r.success:
                    continue
                
                md = r.markdown[:5000]
                
                # 猪八戒任务链接模式
                task_urls = list(set(re.findall(r'https://task\.zbj\.com/\w+/t\d+\.html', md)))
                
                for task_url in task_urls[:5]:
                    if task_url in seen:
                        continue
                    seen.add(task_url)
                    
                    try:
                        r2 = await crawler.arun(task_url, config=run_cfg)
                        if not r2.success:
                            continue
                        
                        md2 = r2.markdown[:3000]
                        
                        # 提取标题
                        title_m = re.search(
                            r'<h1[^>]*>([^<]{5,80})|'
                            r'class="[^"]*title[^"]*"[^>]*>([^<]{5,80})|'
                            r'招标项目[^：]*：\s*([^\n<]{5,80})',
                            md2
                        )
                        title = clean(title_m.group(1) or title_m.group(2) or title_m.group(3) or "未获取") if title_m else "未获取"
                        
                        # 提取金额
                        salary_m = re.search(
                            r'(?:预算|报价|价格|金额)[^：]*：\s*([^元\n]{5,30})|'
                            r'(\d+(?:,\d{3})*\s*[-~至到]\s*\d+(?:,\d{3})*)\s*元|'
                            r'¥\s*(\d+(?:,\d{3})+)',
                            md2
                        )
                        salary = salary_m.group(0).strip() if salary_m else "面议"
                        
                        # 提取雇主/公司
                        company_m = re.search(
                            r'(?:雇主|发包方|客户)[^：]*：\s*([^\n<]{2,30})|'
                            r'class="[^"]*user[^"]*"[^>]*>([^<]{2,30})',
                            md2
                        )
                        company = clean(company_m.group(1) or company_m.group(2) or "匿名雇主")[:30]
                        
                        # 提取描述
                        desc_lines = [l.strip() for l in md2.split('\n') if 10 < len(l.strip()) < 150]
                        desc = ' | '.join(desc_lines[:3])
                        
                        jobs.append({
                            "platform": "猪八戒",
                            "title": title,
                            "salary": salary,
                            "company": company,
                            "description": desc[:150],
                            "url": task_url,
                            "category": cat,
                            "lang": "zh",
                            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "currency": "CNY",
                            "type": "招标/接单",
                        })
                        
                        await asyncio.sleep(0.5)
                    except Exception:
                        pass
                        
            except Exception:
                pass
    
    return jobs

async def crawl_ipweike_tasks() -> List[Dict]:
    """爬取一品威客任务"""
    jobs = []
    seen = set()
    browser_cfg = BrowserConfig(headless=True, verbose=False)
    run_cfg = CrawlerRunConfig(verbose=False, page_timeout=20000)
    
    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        cats = PLATFORMS["ipweike"]["categories"]
        
        for cat in cats:
            url = f"https://www.epwk.com/{cat}/"
            try:
                r = await crawler.arun(url, config=run_cfg)
                if not r.success:
                    continue
                
                md = r.markdown[:5000]
                
                # 一品威客任务链接模式
                task_urls = list(set(re.findall(r'https://www\.epwk\.com/\w+/\d+\.html', md)))
                
                for task_url in task_urls[:5]:
                    if task_url in seen:
                        continue
                    seen.add(task_url)
                    
                    try:
                        r2 = await crawler.arun(task_url, config=run_cfg)
                        if not r2.success:
                            continue
                        
                        md2 = r2.markdown[:3000]
                        
                        # 提取标题
                        title_m = re.search(
                            r'<h1[^>]*>([^<]{5,80})|'
                            r'class="[^"]*title[^"]*"[^>]*>([^<]{5,80})|'
                            r'任务名称[^：]*：\s*([^\n<]{5,80})',
                            md2
                        )
                        title = clean(title_m.group(1) or title_m.group(2) or title_m.group(3) or "未获取") if title_m else "未获取"
                        
                        # 提取金额
                        salary_m = re.search(
                            r'(?:预算|报价|赏金|金额)[^：]*：\s*([^元\n]{5,30})|'
                            r'(\d+(?:,\d{3})*\s*[-~至到]\s*\d+(?:,\d{3})*)\s*元|'
                            r'¥\s*(\d+(?:,\d{3})+)',
                            md2
                        )
                        salary = salary_m.group(0).strip() if salary_m else "面议"
                        
                        # 提取雇主
                        company_m = re.search(
                            r'(?:雇主|发布者|客户)[^：]*：\s*([^\n<]{2,30})|'
                            r'class="[^"]*nickname[^"]*"[^>]*>([^<]{2,30})',
                            md2
                        )
                        company = clean(company_m.group(1) or company_m.group(2) or "匿名雇主")[:30]
                        
                        # 提取描述
                        desc_lines = [l.strip() for l in md2.split('\n') if 10 < len(l.strip()) < 150]
                        desc = ' | '.join(desc_lines[:3])
                        
                        jobs.append({
                            "platform": "一品威客",
                            "title": title,
                            "salary": salary,
                            "company": company,
                            "description": desc[:150],
                            "url": task_url,
                            "category": cat,
                            "lang": "zh",
                            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "currency": "CNY",
                            "type": "招标/接单",
                        })
                        
                        await asyncio.sleep(0.5)
                    except Exception:
                        pass
                        
            except Exception:
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