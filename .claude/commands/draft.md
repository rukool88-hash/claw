---
description: 写作辅助 — 从项目素材生成初稿到 output/<type>/
---

# /draft <type> <topic>

执行 [CLAUDE.md](../../CLAUDE.md) 第 4.4 节定义的"写作辅助"流程。

## 参数
- `<type>` ∈ `cep | whitepaper | script | blog`
- `<topic>`：项目 slug 或自由主题

## 输入素材
按优先级读取：
1. `projects/<topic>/debate.md`（若存在）
2. `projects/<topic>/outline.md`（若存在）
3. 用户在调用时传入的额外要点
4. `knowledge/` 中相关卡片（双链匹配）

## 输出
- 文件：`output/<type>/YYYY-MM-DD-<slug>.md`
- frontmatter：`status: draft`

## 风格规则
| type | 长度 | 结构 |
|---|---|---|
| blog | ≤ 2500 字 | 钩子开头 → 3–5 小标题 → CTA 结尾 |
| cep | ≤ 3000 字 | 定义 → 问题 → 概念框架 → 含义 |
| whitepaper | 不限 | 摘要 → 背景 → 方法 → 数据 → 结论 → 参考 |
| script | ≤ 8 分钟 | 分镜：[画面]/[旁白]/[字幕] |

## 收尾
文末必须列出 **3 个待用户决策的问题**（标题、CTA、配图、引用源等）。
