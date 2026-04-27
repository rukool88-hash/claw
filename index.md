---
github_repo: rukool88-hash|https://github.com/rukool88-hash/claw
---
# Index — 各目录导航

| 目录 | 用途 | AI 是否写入 |
|---|---|---|
| [articles/](articles/) | 长文 / 已发布文章源文件（人类主导，AI 只读） | 否 |
| [fleeting-notes/](fleeting-notes/) | 浮墨笔记 — 瞬时想法、临时记录 | 否（只读参考） |
| [knowledge/](knowledge/) | 知识卡片（Atomic notes） | **是** — `/maintain` 维护 |
| [inbox/ideas.md](inbox/ideas.md) | 灵感池 — 待加工的话题种子 | **是** — `/ideate` 追加 |
| [inbox/audio/](inbox/audio/) | 待转写音频（不入 Git） | n8n 写入 |
| [inbox/transcripts/](inbox/transcripts/) | 语音转写结果 | n8n 写入，`/maintain` 消费 |
| [inbox/rss/](inbox/rss/) | RSS / 邮件 / 书摘落地 | n8n 写入，`/maintain` 消费 |
| [projects/](projects/) | 项目库 — 每个主题一个子目录 | **是** — `/debate` `/draft` |
| [output/cep/](output/cep/) | CEP 概念文档 | **是** — `/draft cep` |
| [output/whitepapers/](output/whitepapers/) | 白皮书 / 报告 | **是** — `/draft whitepaper` |
| [output/scripts/](output/scripts/) | 视频脚本 | **是** — `/draft script` |
| [output/blog/](output/blog/) | 博客文章 | **是** — `/draft blog` |

## AI 行为规则
见 [CLAUDE.md](CLAUDE.md)。

## Slash 命令
- [/maintain](.claude/commands/maintain.md) — 知识维护（每天 22:00 自动）
- [/ideate](.claude/commands/ideate.md) — 灵感引擎
- [/debate](.claude/commands/debate.md) — 认知对撞
- [/draft](.claude/commands/draft.md) — 写作辅助
