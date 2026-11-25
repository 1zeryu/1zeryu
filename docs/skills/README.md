# Skills 目录

这里存放本仓库用到的 skill。每个 skill 是一个独立目录，核心是 `SKILL.md`（可选带 `references/` 参考资料或 `scripts/` 脚本）。

按性质分三层，新 skill 按用途归入对应层：

## preferences（习惯 · 规范）

约束长期行为的持久规则，写文章、写代码、协作时主动套用。

| skill | 用途 |
|-------|------|
| user-work-preferences | 记录并迭代维护 yukun.zhou 的工作偏好、协作规则与技术栈约定 |
| blog-style | 技术博客写作规范（结构/段落/术语），用于新文撰写与旧文修订自检 |

## methodology（协作方法论）

和 AI 长期协作的元方法，不是单次操作，而是贯穿项目全过程。

| skill | 用途 |
|-------|------|
| agent-entry-file | 给 AI 写入口文件（AGENTS.md 模式）：读序、红线、改动同步映射、落地前自检、半成品状态 |
| maintenance-log | 给长期项目维护一份可追溯的维护日志（日期 + 改了什么 + 为什么 + 怎么验证） |
| postmortem-loop | 把线上故障按「现象 → 根因 → 修复 → 验证」沉淀成可复用的防御资产 |
| progress-doc | 让 agent 在多步任务中维护可监控的过程文档（计划先行、一步一落、状态可 grep） |

## tasks（具体任务 · 操作）

一件明确的事，有固定步骤清单，按步骤执行。

| skill | 用途 |
|-------|------|
| add-ssh-terminal | 给新服务器配 VSCode/Trae 集成终端，开终端自动 SSH 登录进入指定目录 |
| zhihu-draft-publish | 把 Hugo 博客文章同步到知乎草稿箱（只写草稿，发布/删除需用户确认） |
| research-guide | 深度研究/分析：证据层级、交叉验证、检索范式、子场景路由（官方英文 skill） |
| ci-setup | 给软件项目从零搭建 CI：测试 + 依赖 + workflow 三件套串成 PR 门禁（含 Uranus 案例） |