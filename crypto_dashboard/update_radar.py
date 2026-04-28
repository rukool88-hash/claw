import urllib.request
import urllib.parse
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import os
import time
import re
import email.utils
import sqlite3

# 初始化数据库
DB_PATH = '/workspace/crypto_dashboard/crypto_news.db'
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS news (
        link TEXT PRIMARY KEY,
        source TEXT,
        original_title TEXT,
        zh_title TEXT,
        pub_date TEXT,
        parsed_dt TIMESTAMP,
        original_desc TEXT,
        zh_desc TEXT,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()

def strip_html(text):
    if not text: return ""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', text).strip()

def is_chinese(text):
    # 简单判断是否包含中文字符
    return any('\u4e00' <= char <= '\u9fff' for char in str(text))

def translate_text(text):
    if not text: return ""
    if is_chinese(text): 
        return text # 如果已经是中文源，直接返回不翻译
        
    try:
        url = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=zh-CN&dt=t&q=" + urllib.parse.quote(text)
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            return ''.join([sentence[0] for sentence in data[0] if sentence[0]])
    except Exception as e:
        return text

def fetch_all_rss():
    # 扩展：加入了国内头部加密媒体 Odaily 和 谷歌中文加密资讯聚合
    sources = [
        ("Cointelegraph", "https://cointelegraph.com/rss"),
        ("CoinDesk", "https://www.coindesk.com/arc/outboundfeeds/rss/"),
        ("Bitcoin.com", "https://news.bitcoin.com/feed/"),
        ("Odaily星球日报", "https://www.odaily.news/feed"),
        ("Google中文资讯", "https://news.google.com/rss/search?q=%E5%8A%A0%E5%AF%86%E8%B4%A7%E5%B8%81+OR+%E6%AF%94%E7%89%B9%E5%B8%81+OR+Web3+when:1d&hl=zh-CN&gl=CN&ceid=CN:zh-Hans")
    ]
    
    all_items = []
    print("📡 正在从全球与国内源抓取数据...")
    for source_name, url in sources:
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            with urllib.request.urlopen(req, timeout=10) as response:
                tree = ET.parse(response)
                root = tree.getroot()
                # 中文源稍微多抓几条
                limit = 12 if 'Odaily' in source_name or 'Google' in source_name else 8
                
                for item in root.findall('.//item')[:limit]:
                    title = item.find('title').text if item.find('title') is not None else ''
                    link = item.find('link').text if item.find('link') is not None else '#'
                    pubDate = item.find('pubDate').text if item.find('pubDate') is not None else ''
                    desc = item.find('description').text if item.find('description') is not None else ''
                    
                    try:
                        dt = email.utils.parsedate_to_datetime(pubDate)
                    except:
                        dt = datetime.now()
                        
                    all_items.append({
                        'source': source_name,
                        'title': title,
                        'link': link,
                        'date': pubDate,
                        'dt': dt,
                        'desc': strip_html(desc)
                    })
        except Exception as e:
            print(f"[{source_name}] 抓取失败: {e}")
            
    all_items.sort(key=lambda x: x['dt'], reverse=True)
    
    print("🔤 检查数据库并翻译海外内容...")
    for item in all_items:
        cursor.execute("SELECT link FROM news WHERE link=?", (item['link'],))
        if cursor.fetchone() is None:
            print(f"New article found: {item['title'][:20]}...")
            zh_title = translate_text(item['title'])
            short_desc = item['desc'][:300] + ('...' if len(item['desc']) > 300 else '')
            zh_desc = translate_text(short_desc)
            
            cursor.execute('''
                INSERT INTO news (link, source, original_title, zh_title, pub_date, parsed_dt, original_desc, zh_desc)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (item['link'], item['source'], item['title'], zh_title, item['date'], item['dt'].isoformat(), item['desc'], zh_desc))
            conn.commit()
            if not is_chinese(item['title']):
                time.sleep(0.3) # 只有翻译API才需要限速等待

def fetch_trending_coins():
    try:
        req = urllib.request.Request('https://api.coingecko.com/api/v3/search/trending', headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            return [{'name': coin['item']['name'], 'symbol': coin['item']['symbol'], 'market_cap_rank': coin['item']['market_cap_rank']} for coin in data['coins'][:8]]
    except Exception as e:
        return [{'name': f'趋势获取错误: {e}', 'symbol': 'ERR', 'market_cap_rank': 0}]

fetch_all_rss()
trending = fetch_trending_coins()

cursor.execute("SELECT source, zh_title, link, pub_date, zh_desc FROM news ORDER BY parsed_dt DESC LIMIT 35")
saved_news = cursor.fetchall()
now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Crypto Radar - Dashboard</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: #e2e8f0; padding: 30px; margin: 0; }}
        .container {{ max-width: 1200px; margin: auto; }}
        .layout-grid {{ display: grid; grid-template-columns: 2fr 1fr; gap: 25px; }}
        @media (max-width: 900px) {{ .layout-grid {{ grid-template-columns: 1fr; }} }}
        .card {{ background: #1e293b; padding: 25px; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); border: 1px solid #334155; height: fit-content; }}
        a {{ color: #38bdf8; text-decoration: none; font-weight: 600; line-height: 1.4; font-size: 1.1em; }}
        a:hover {{ color: #7dd3fc; text-decoration: underline; }}
        h1 {{ color: #f8fafc; border-bottom: 2px solid #334155; padding-bottom: 15px; font-size: 2em; }}
        h2 {{ color: #cbd5e1; margin-top: 0; font-size: 1.3em; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #334155; padding-bottom: 10px; margin-bottom: 15px; }}
        .db-badge {{ background: #10b981; color: white; padding: 4px 10px; border-radius: 6px; font-size: 0.6em; font-weight: normal; }}
        .item {{ margin-bottom: 20px; padding-bottom: 15px; border-bottom: 1px solid #334155; }}
        .item:last-child {{ border-bottom: none; margin-bottom: 0; padding-bottom: 0; }}
        .meta {{ font-size: 0.85em; color: #64748b; margin-top: 8px; display: flex; align-items: center; gap: 10px; }}
        .source-tag {{ background: #475569; color: #f8fafc; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 0.9em; }}
        .source-tag.Odaily星球日报 {{ background: #2563eb; }}
        .source-tag.Google中文资讯 {{ background: #ea4335; }}
        .source-tag.CoinDesk {{ background: #047857; }}
        .source-tag.Cointelegraph {{ background: #b45309; }}
        .source-tag.Bitcoin-com {{ background: #d97706; }}
        .desc {{ font-size: 0.95em; color: #94a3b8; margin-top: 8px; line-height: 1.5; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 15px; }}
        .coin-box {{ background: #0f172a; padding: 15px; border-radius: 8px; border: 1px solid #334155; display: flex; justify-content: space-between; align-items: center; }}
        .coin-name {{ font-weight: 600; font-size: 1.1em; color: #f1f5f9; }}
        .coin-symbol {{ color: #64748b; font-size: 0.9em; }}
        .rank-badge {{ background: #334155; padding: 4px 10px; border-radius: 20px; font-size: 0.8em; color: #38bdf8; }}
        .twitter-container {{ height: 800px; overflow-y: auto; background: #0f172a; border-radius: 8px; padding: 10px; border: 1px solid #334155; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 币圈全景雷达 (Crypto Radar)</h1>
        <p style="color: #94a3b8;">海内外双语源聚合、数据库永久归档、X(推特)大V实时监控 | 最后更新: {now}</p>

        <div class="card">
            <h2>🔥 资金热捧项目 (CoinGecko Top Trending)</h2>
            <div class="grid">
"""

for c in trending:
    html += f"""
                <div class="coin-box">
                    <div>
                        <div class="coin-name">{c["name"]}</div>
                        <div class="coin-symbol">{c["symbol"]}</div>
                    </div>
                    <div class="rank-badge">Rank #{c["market_cap_rank"]}</div>
                </div>
    """

html += """
            </div>
        </div>
        
        <div class="layout-grid">
            <!-- 左侧：全球+国内新闻流 -->
            <div class="card">
                <h2>
                    <span>📰 24H 实时前沿动态 (海内外)</span>
                    <span class="db-badge">SQLite 已归档</span>
                </h2>
"""

for row in saved_news:
    source, zh_title, link, pub_date, zh_desc = row
    tag_class = source.replace('.', '-')
    html += f"""
                <div class="item">
                    <a href="{link}" target="_blank">▪ {zh_title}</a>
                    <div class="desc">{zh_desc}</div>
                    <div class="meta">
                        <span class="source-tag {tag_class}">{source}</span>
                        <span>{pub_date}</span>
                    </div>
                </div>
"""

html += """
            </div>

            <!-- 右侧：X (Twitter) KOL 实时信息流 -->
            <div class="card">
                <h2>🐦 X (Twitter) 大V 实盘与观点流</h2>
                <div class="twitter-container">
                    <a class="twitter-timeline" data-theme="dark" href="https://twitter.com/WuBlockchain?ref_src=twsrc%5Etfw">Tweets by WuBlockchain (吴说区块链)</a>
                    <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>
                    <br><hr style="border-color:#334155;"><br>
                    <a class="twitter-timeline" data-theme="dark" href="https://twitter.com/VitalikButerin?ref_src=twsrc%5Etfw">Tweets by Vitalik Buterin</a>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""

html_path = os.path.expanduser('/workspace/crypto_dashboard/index.html')
with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)

conn.close()
print(f"✅ Dashboard generated successfully at: {html_path}")
