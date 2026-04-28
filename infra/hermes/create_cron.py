"""Create the pkm-maintain cron job via Hermes internal API.
Run inside the ubuntu24 container as root.
"""
import json
import sys

sys.path.insert(0, "/usr/local/lib/hermes-agent")

from tools.cronjob_tools import cronjob

PROMPT = (
    "执行 /maintain：扫描 inbox/transcripts 与 inbox/rss 中未处理的文件，"
    "按 /workspace/CLAUDE.md 第 4.1 节流程处理（最多 10 个），"
    "并把已处理文件移动到 _processed/。"
    "完成后把维护摘要发回 Telegram。"
)

# Remove any prior pkm-maintain to keep idempotent
existing = json.loads(cronjob(action="list", include_disabled=True))
for j in existing.get("jobs", []) or []:
    if j.get("name") == "pkm-maintain":
        cronjob(action="remove", job_id=j["id"])
        print(f"Removed prior job: {j['id']}")

result = json.loads(
    cronjob(
        action="create",
        schedule="0 22 * * *",
        prompt=PROMPT,
        name="pkm-maintain",
        deliver="telegram",
        skills=["pkm-vault"],
        workdir="/workspace",
    )
)
print(json.dumps(result, ensure_ascii=False, indent=2))
