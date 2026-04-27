---
description: 灵感引擎 — 随机组合知识卡片生成新话题，追加到 inbox/ideas.md
---

# /ideate

执行 [CLAUDE.md](../../CLAUDE.md) 第 4.2 节定义的"灵感引擎"流程：

1. 从 `knowledge/` 随机抽 2–3 张卡（优先近 7 天 `updated` 的）。
2. 强制建立 **非显然** 关联：跨域、反直觉、矛盾点。
3. 产出 1 个有张力的话题，**追加** 到 `inbox/ideas.md` 末尾。

## 输出格式（严格）

```markdown
## YYYY-MM-DD HH:mm — <话题标题>

- **来源卡片**：[[card1]] × [[card2]]
- **核心张力**：一句话。
- **可能角度**：
  - …
  - …
  - …
- **下一步**：`/debate <slug>` 或 `/draft blog <slug>`
```

## 参数
- `--seed <概念>`：强制以某张卡为种子。
- `--n <数量>`：一次产出多个话题（默认 1）。

## 边界
- **不要覆盖** ideas.md 中已有内容，只能追加。
