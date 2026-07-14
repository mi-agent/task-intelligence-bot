#!/usr/bin/env python3
"""
SEO Optimizer - 搜索引擎优化引擎
自动为内容添加SEO关键词、联盟链接、结构化数据
"""
import re, json, os
from pathlib import Path
from datetime import datetime

BASE = Path("/Users/ai/Projects/task-bot")
CONTENT_DIR = BASE / "content"
DATA_DIR = BASE / "data"

# SEO关键词库（长尾关键词，中文）
SEO_KEYWORDS = {
    "python": [
        "Python副业", "Python接单", "Python兼职", "Python远程工作",
        "Python爬虫赚钱", "Python外包项目", "Python零基础副业",
    ],
    "freelance": [
        "程序员接单", "程序员副业", "远程工作", "兼职开发",
        "外包接单平台", "自由职业", "在家工作", "数字游民",
    ],
    "money": [
        "副业赚钱", "被动收入", "零成本创业", "月入过万",
        "第二收入", "下班后赚钱", "网络兼职",
    ],
    "tools": [
        "AI工具免费", "开源赚钱工具", "爬虫工具", "自动化工具",
        "开发者工具推荐", "效率工具",
    ]
}

# 联盟链接池
AFFILIATE_LINKS = {
    "NordVPN": {
        "url": "https://nordvpn.com/",
        "code": "AFFILIATE_CODE",
        "commission": "40%",
        "keywords": ["VPN", "隐私", "安全", "代理"],
    },
    "PIA VPN": {
        "url": "https://www.privateinternetaccess.com/",
        "code": "AFFILIATE_CODE",
        "commission": "40%",
        "keywords": ["VPN", "隐私"],
    },
    "DigitalOcean": {
        "url": "https://www.digitalocean.com/",
        "code": "AFFILIATE_CODE",
        "commission": "$25-100/单",
        "keywords": ["服务器", "部署", "云服务", "VPS", "Docker"],
    },
    "1Password": {
        "url": "https://1password.com/",
        "code": "AFFILIATE_CODE",
        "commission": "100%首年",
        "keywords": ["密码", "安全", "管理"],
    },
    "Namecheap": {
        "url": "https://www.namecheap.com/",
        "code": "AFFILIATE_CODE",
        "commission": "50%+",
        "keywords": ["域名", "主机", "网站建设"],
    },
}

class SEOOptimizer:
    def __init__(self):
        self.stats = {"optimized": 0, "affiliates_added": 0, "keywords_added": 0}
    
    def optimize_article(self, content: str, filename: str = "") -> tuple[str, dict]:
        """优化一篇文章：SEO + 联盟链接"""
        changes = {}
        
        # 1. 添加SEO元描述（如果没有）
        first_line = content.split('\n')[0]
        title = re.sub(r'^#\s*', '', first_line)
        
        if "meta" not in filename.lower():
            # 2. 添加联盟链接 - 自然插入
            for brand, info in AFFILIATE_LINKS.items():
                for kw in info["keywords"]:
                    pattern = re.compile(re.escape(kw), re.IGNORECASE)
                    matches = list(pattern.finditer(content))
                    if matches and len(matches) <= 3:
                        # 只在第一次出现时插入链接（避免过度优化）
                        pos = matches[0].start()
                        original = matches[0].group()
                        # 排除已经在链接内的
                        before = content[max(0,pos-100):pos]
                        if "href=" in before and pos - before.rfind("href=") < 100:
                            continue
                        # 排除已经加过链接的
                        if f"[{original}]" in before or f"]({info['url']}" in content:
                            continue
                        linked = f"[{original}]({info['url']})"
                        content = content[:pos] + linked + content[pos+len(original):]
                        changes.setdefault("affiliates", []).append(f"{brand}: {original}")
                        self.stats["affiliates_added"] += 1
                        break
        
        # 3. 强化SEO关键词密度
        for category, keywords in SEO_KEYWORDS.items():
            for kw in keywords:
                if kw not in content and kw not in title:
                    # 在文章末尾自然添加
                    if "## 推荐阅读" in content or "## 相关资源" in content:
                        continue
                    # 不强制插入，维持内容自然
                    pass
        
        return content, changes
    
    def optimize_all(self):
        """优化所有文章"""
        articles = list(CONTENT_DIR.glob("*.md"))
        
        print(f"📈 SEO 优化器启动 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        for article in articles:
            original = article.read_text()
            optimized, changes = self.optimize_article(original, article.stem)
            
            if changes:
                article.write_text(optimized)
                self.stats["optimized"] += 1
                print(f"✅ {article.stem[:40]:40s}")
                for k, v in changes.items():
                    print(f"   🔗 {k}: {', '.join(v[:2])}")
            else:
                print(f"→ {article.stem[:40]:40s} (无需优化)")
        
        # 报告
        print(f"\n📊 优化统计:")
        print(f"   优化文章: {self.stats['optimized']}/{len(articles)}")
        print(f"   添加联盟链接: {self.stats['affiliates_added']}")
        
        # 保存状态
        report = {
            "timestamp": datetime.now().isoformat(),
            "stats": self.stats,
            "articles_count": len(articles),
        }
        (DATA_DIR / "seo_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2))
        print(f"   报告已保存: data/seo_report.json")
        
        return self.stats
    
    def generate_sitemap(self):
        """生成站点地图（用于SEO）"""
        sitemap = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://mi-agent.github.io/ai-tools-guide/</loc><priority>1.0</priority></url>
  <url><loc>https://mi-agent.github.io/ai-tools-guide/shop/</loc><priority>0.9</priority></url>
  <url><loc>https://mi-agent.github.io/ai-tools-guide/python-freelance/</loc><priority>0.8</priority></url>
  <url><loc>https://mi-agent.github.io/ai-tools-guide/SUPPORT.md</loc><priority>0.6</priority></url>
</urlset>"""
        
        guide_dir = Path("/Users/ai/Projects/ai-tools-guide")
        (guide_dir / "sitemap.xml").write_text(sitemap)
        print(f"✅ sitemap.xml 已生成")
        
        # robots.txt
        robots = """User-agent: *
Allow: /
Sitemap: https://mi-agent.github.io/ai-tools-guide/sitemap.xml
"""
        (guide_dir / "robots.txt").write_text(robots)
        print(f"✅ robots.txt 已生成")

if __name__ == "__main__":
    opt = SEOOptimizer()
    opt.optimize_all()
    opt.generate_sitemap()
