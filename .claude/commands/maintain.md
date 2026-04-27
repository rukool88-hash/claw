---
description: 知识维护 — 扫描 inbox 抽取概念到 knowledge/，处理后归档
---

# /maintain

执行 [CLAUDE.md](../../CLAUDE.md) 第 4.1 节定义的"知识维护"流程：

1. 扫描 `inbox/transcripts/` 与 `inbox/rss/`（不含 `_processed/`），列出未处理文件。
2. **本次最多处理 10 个**（按修改时间从旧到新优先）。
3. 抽取概念 → 在 `knowledge/` 新建或更新 Atomic 卡片。
4. 处理完毕的原文件 **移动**（非删除）到对应 `_processed/` 子目录。
5. 末尾输出维护摘要：

```
处理文件: N 个
新增卡片: M 张 ([[卡1]], [[卡2]] ...)
更新卡片: K 张 ([[卡a]] ...)
跳过文件: ...
```

## 参数
- `--dry-run`：仅列出将处理的文件与计划，不实际写入。
- `--limit <N>`：覆盖默认 10 个上限。

## 边界
- 严禁修改 `articles/` 与 `fleeting-notes/`。
- 严禁删除 inbox 原文件。
