---
description: 认知对撞 — 多角色独立 AI 视角辩论 + 现实检验
---

# /debate <topic>

执行 [CLAUDE.md](../../CLAUDE.md) 第 4.3 节定义的"认知对撞"流程。

## 输入
- `<topic>`：话题标题或 slug。若不存在 `projects/<slug>/`，自动创建。

## 流程
1. 在 `projects/<topic-slug>/debate.md` 中按顺序生成四个独立段落（每个段落独立思考，不参考前段结论）：
   1. **🟢 红队（Bull）**：3 条最强支持论据 + 数据/案例引用。
   2. **🔴 蓝队（Bear）**：3 条最强反驳论据 + 数据/案例引用。
   3. **🟡 怀疑派**：指出双方共同未验证的前提与认知盲区。
   4. **🔵 现实检验**：列出 2–3 个 **可用公开数据源验证** 的具体问题。
2. 最后一段 `## 综合结论` 给出加权判断 + 下一步问题清单。

## 参数
- `--with-research`：允许使用网络检索补充数据（默认禁用）。
- `--rounds <N>`：进行 N 轮反复对撞（默认 1）。

## 输出文件 frontmatter
```yaml
---
created: <now>
type: project
status: debating
tags: [debate, <主题tag>]
---
```
