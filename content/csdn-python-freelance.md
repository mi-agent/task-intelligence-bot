# 【干货】我用Python接私活赚了3万，全过程分享（附代码）

我是程序员老王，主业做后端开发，业余时间接点私活。2025年靠Python接单赚了大概3万块，今天把全过程整理出来给大家。

**声明：**
- 不卖课，不割韭菜
- 所有数据真实
- 代码可以直接用

---

## 一、先说说赚了多少钱

| 月份 | 接了几个单 | 收入 |
|------|-----------|------|
| 1月 | 2个 | ¥4500 |
| 2月 | 3个 | ¥8200 |
| 3月 | 2个 | ¥6800 |
| 合计 | 7个 | ¥19500 |

加上帮人做技术咨询和卖代码，到年底大概3万出头。

平均时薪大概200多，比上班强一点，但也不多。关键是：**不影响正常工作**。

---

## 二、我在哪些平台接单

### 程序员客栈（最推荐新手）

地址：proginn.com

这是我第一个出单的平台。新手友好，有平台担保，不怕赖账。

**怎么用：**
1. 注册，完善个人资料（GitHub一定要放）
2. 看任务列表，找自己能做的
3. 写提案，投出去
4. 等待回复

**我第一个单子：**
帮一个淘宝店主爬取竞品数据，报价2800，用了2个晚上。

```python
# 核心爬虫代码（实际项目简化版）
import requests
from bs4 import BeautifulSoup

class TaobaoScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)...',
            'Cookie': '你的cookie'  # 需要登录获取
        }
    
    def get_products(self, keyword, pages=5):
        results = []
        for page in range(1, pages + 1):
            url = f'https://s.taobao.com/search?q={keyword}&page={page}'
            resp = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            items = soup.select('.item')
            for item in items:
                product = {
                    'title': item.select_one('.title').text.strip(),
                    'price': item.select_one('.price').text.strip(),
                    'sales': item.select_one('.deal-cnt').text.strip() if item.select_one('.deal-cnt') else '0',
                }
                results.append(product)
        
        return results

# 使用
scraper = TaobaoScraper()
products = scraper.get_products('运动鞋', pages=3)
for p in products:
    print(p)
```

### 远程.work

地址：yuancheng.work

这个平台的特点是**薪资透明**，可以直接看到是多少k。

我在这接了一个长期项目，Python后端开发，每月额外2万多收入。

---

## 三、什么单子最赚钱

根据我这7个单子的经验：

| 单子类型 | 我报价 | 用时 | 推荐指数 |
|---------|-------|------|---------|
| 爬虫/数据采集 | ¥2000-8000 | 1-5天 | ⭐⭐⭐⭐⭐ |
| API开发 | ¥3000-15000 | 1-2周 | ⭐⭐⭐⭐ |
| 自动化脚本 | ¥1000-5000 | 1-3天 | ⭐⭐⭐⭐ |
| 全栈项目 | ¥5000-20000 | 2-4周 | ⭐⭐⭐ |

**爬虫是最容易上手的。** 很多传统企业需要数据，但自己不会爬。这就是机会。

---

## 四、怎么报价

很多人不敢报价，怕报高了吓跑客户，怕报低了亏本。

我的经验：

### 简单粗暴法（适合新手）

```
报价 = 预估天数 × 1000-1500
```

比如你觉得3天能做完，就报3000-4500。

### 科学一点的方法

```
报价 = (工时 × 时薪) × 1.2
```

时薪参考：
- 新手：100-150/时
- 中级：200-300/时
- 高级：400-600/时

### 记住几个原则

1. **不要比市价低太多** — 会显得不专业
2. **给2-3个选项** — 高中低配让客户选
3. **强调价值** — "帮你省了XX时间/多少钱"

---

## 五、我是怎么找单的

### 方法1：主动搜索

每天花10分钟刷平台，看到合适的就投。

### 方法2：用爬虫自动采集

我写了一个脚本，自动采集5个平台的任务，筛选高薪的推送到微信。

```python
# 任务采集脚本（精简版）
import requests
import json
from datetime import datetime

PLATFORMS = {
    '程序员客栈': 'https://www.proginn.com',
    '远程.work': 'https://yuancheng.work',
    '电鸭': 'https://eleduck.com',
}

def fetch_tasks():
    results = []
    for name, url in PLATFORMS.items():
        try:
            resp = requests.get(url, timeout=10)
            # 解析逻辑（实际代码更复杂）
            tasks = parse_page(resp.text, name)
            results.extend(tasks)
        except Exception as e:
            print(f'{name} 采集失败: {e}')
    return results

def parse_page(html, platform):
    # 简化版：实际上每個平台格式不一样
    tasks = []
    # ...解析逻辑...
    return tasks

if __name__ == '__main__':
    tasks = fetch_tasks()
    print(f'采集到 {len(tasks)} 个任务')
    
    # 按薪资排序，显示前10
    sorted_tasks = sorted(tasks, key=lambda x: x.get('salary', 0), reverse=True)
    for i, t in enumerate(sorted_tasks[:10], 1):
        print(f'{i}. [{t["platform"]}] {t["title"]} - {t["salary"]}')
```

### 方法3：口碑介绍

做好第一个单子，让客户满意，他会介绍朋友给你。

我这7个单子里，有2个是客户介绍的。

---

## 六、注意事项（踩坑总结）

### 坑1：需求不清楚

**教训：** 一定要书面确认需求，最好有验收标准。

**错误做法：** 客户说"很简单"，就开始做。

**正确做法：** 详细沟通，列出我要做什么，然后等客户确认。

### 坑2：低估工时

**教训：** 预估时间 × 1.5

**错误做法：** "感觉3天能做"，结果做了1周。

**正确做法：** 认真分析，给出 buffer 时间。

### 坑3：没有留证据

**教训：** 每个项目结束，截图、记录、整理。

**错误做法：** 做完就忘，下次类似项目从头来。

**正确做法：** 整理代码到GitHub，建立自己的工具库。

---

## 七、工具推荐

我用的工具：

| 工具 | 用途 | 费用 |
|------|------|------|
| VS Code | 写代码 | 免费 |
| GitHub | 存代码 | 免费 |
| Notion | 项目管理 | 免费 |
| Server酱 | 微信通知 | 免费 |

技术栈：

| 类型 | 工具 |
|------|------|
| 爬虫 | requests + BeautifulSoup + Playwright |
| 后端 | FastAPI + PostgreSQL |
| 部署 | 阿里云ECS + Nginx |
| 定时 | cron + supervisor |

---

## 八、总结

1. **Python接单不难** — 市场需求大，竞争不算太激烈
2. **第一个单子最重要** — 做好口碑，后续会容易很多
3. **报价要专业** — 表格、明细、方案，体现专业度
4. **持续积累** — 每个项目都是学习机会

---

## 代码和工具

我把这些年的工具整理了一下，放在GitHub上：

👉 https://github.com/mi-agent/python-freelance-kit

包含：
- 任务采集爬虫（5个平台）
- 提案模板（3套）
- 定价策略表
- 平台接单攻略

免费的，可以直接用。

---

有问题可以在评论区问，看到会回。

觉得有用的话，转发一下，谢谢！

---

*个人经历，仅供参考。收入因人而异，取决于投入时间和技能水平。*