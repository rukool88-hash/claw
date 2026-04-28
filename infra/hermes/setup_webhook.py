"""Enable webhook platform in Hermes config and create rss-ingest subscription."""
import json
import sys
import yaml
from pathlib import Path

CONFIG = Path("/root/.hermes/config.yaml")
SUBS = Path("/root/.hermes/webhook_subscriptions.json")

# 1. Enable webhook platform
cfg = yaml.safe_load(CONFIG.read_text())
cfg.setdefault("platforms", {})
cfg["platforms"]["webhook"] = {
    "enabled": True,
    "extra": {"host": "0.0.0.0", "port": 8644},
}
CONFIG.write_text(yaml.dump(cfg, allow_unicode=True, sort_keys=False))
print("✓ Enabled platforms.webhook (port 8644)")

# 2. Create / overwrite rss-ingest subscription
import secrets
import time

PROMPT = (
    "新 RSS 文章到达。请按以下规则**仅归档不评论**：\n\n"
    "1. 在 /workspace/inbox/rss/ 下新建文件 YYYY-MM-DD-<slug>.md（slug 取自标题，小写、空格转 -、去标点；最长 60 字符）。\n"
    "2. 文件 frontmatter:\n"
    "   ---\n"
    "   created: <当前时间 YYYY-MM-DD HH:mm>\n"
    "   type: idea\n"
    "   source: rss\n"
    "   url: {url}\n"
    "   feed: {feed_title}\n"
    "   tags: [rss, unprocessed]\n"
    "   status: unprocessed\n"
    "   ---\n"
    "3. 正文 = '# {title}' + 空行 + 文章 content 原文（不要总结/翻译）。\n"
    "4. 完成后回复一行：'✓ rss/<filename>'。\n\n"
    "Payload 字段：title={title}，url={url}，content={content}，feed_title={feed_title}。"
)

subs = {}
if SUBS.exists():
    try:
        subs = json.loads(SUBS.read_text())
    except Exception:
        subs = {}

route = {
    "description": "RSS feed -> /workspace/inbox/rss/ markdown file",
    "events": [],
    "secret": (subs.get("rss-ingest", {}).get("secret") or secrets.token_urlsafe(32)),
    "prompt": PROMPT,
    "skills": ["pkm-vault"],
    "deliver": "log",
    "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
}
subs["rss-ingest"] = route
SUBS.write_text(json.dumps(subs, indent=2, ensure_ascii=False))
print(f"✓ Subscription rss-ingest written.")
print(f"  URL:    http://localhost:8644/webhooks/rss-ingest")
print(f"  Secret: {route['secret']}")
