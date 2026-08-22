---
name: bflabs-agent-readiness
slug: bflabs-agent-readiness
version: 0.4.4
displayName: BFLabs Agent Readiness
summary: 免费诊断网站是否对 AI Agent 可发现、可理解、可操作，并把证据与唯一下一步交给 Agent。
tags: [GEO, Agent Readiness, Website Audit, MCP, SEO]
license: MIT
homepage: https://readiness.bflabs.cn
iconUrl: https://skillhub-1388575217.cos.accelerate.myqcloud.com/skill-icons/uploads/636363/6ee92b9fe5dd4db8af1a35ec6cb5d7d4.png
platforms: [WorkBuddy, Codex, Claude Code, Cursor]
description: Diagnose and improve whether a product website is discoverable, understandable, and actionable by AI agents. Use when auditing a public website or repository, routing evidence-backed GEO repairs, exposing approved WebMCP tools, or verifying a readiness report. Not for ranking guarantees, bulk SEO content, hidden admin exposure, autonomous payments, production traffic changes, or business-outcome attribution without independent evidence.
metadata:
  short-description: Diagnose, improve, and verify AI-agent website readiness
  sunny_skill_type: library
---

# BFLabs Agent Readiness

检查网站能不能被 AI Agent 找到、读懂和用起来。你可以提交公开网址、网站仓库或旧报告。系统会先记录证据，再把任务交给一个最小、最合适的子 Skill。

打开 https://readiness.bflabs.cn 就能免费诊断。也可以从 SkillHub 安装本 Skill，或通过 CLI、MCP 读取同一份报告。

## 三层结果，不要混在一起

- **Agent Readiness**：网站是否可发现、可理解、可操作。这三轴分别判断，不合成一个神秘总分。
- **AI Visibility / GEO Measurement**：真实 AI 平台是否引用或推荐网站。免费诊断默认不测这一层，状态保持为 `not_measured`。
- **Business Outcome**：是否带来线索、转化和收入。没有客户授权的业务数据，状态保持为 `not_measured`。

准备度不是排名，也不承诺推荐、流量、转化或收入。缺少证据时明确标为未知，不会把猜测写成结论。

## 怎么用

1. 提供公开网址、网站仓库或旧报告。
2. 先记录可发现、可理解、可操作三轴的证据，再判断下一步。
3. 只路由一个最小子 Skill，不一次摊开全部改造。
4. 诊断站生成一段可直接复制的改站提示词，其中包含本次证据、根 Skill 入口和唯一子 Skill 路由。
5. 把提示词交给你自己的 Agent。公网扫描本身只读；只有得到你的明确授权，Agent 才能修改本地仓库，何时部署仍由你决定。
6. 部署后，一键复测当时公开可见的网站，并查看 Before / After。
7. 准备度确认后，如需判断真实平台是否引用或推荐，再进入多平台 GEO measurement。
8. 如需跨系统实施、持续验证或业务归因，联系 BFLabs：hello@bflabs.cn。

## 根入口和六个子 Skill

根 Skill 负责判断意图，并只选择下面一个最小能力。

- [**geo-discover**](https://readiness.bflabs.cn/skills/geo-discover)：基于证据整理用户问题和机会地图，不虚构搜索量。
- [**geo-content**](https://readiness.bflabs.cn/skills/geo-content)：生成有证据支撑的标题、解释、比较、榜单方法、页面蓝图或内容改写，是否发布由用户决定。
- [**geo-measure**](https://readiness.bflabs.cn/skills/geo-measure)：汇总用户提供的真实 AI 平台观察，不自动采样，也不推断因果或业务结果。
- [**seo-plan**](https://readiness.bflabs.cn/skills/seo-plan)：制定有证据边界的技术 SEO 计划，不自动修改生产环境。
- [**geo-optimize**](https://readiness.bflabs.cn/skills/geo-optimize)：在用户批准的本地仓库中检查或修复公开事实、结构化信息、robots、sitemap、llms.txt 和准备度问题。
- [**webmcp-enable**](https://readiness.bflabs.cn/skills/webmcp-enable)：实现或核验 MCP、WebMCP 与代表性 Agent 任务；启用外部服务或修改生产环境必须再次获得明确授权。

<!-- Agent-only local routing:
Read references/routing.md before choosing one child Skill. Read references/product-boundary.md before making product claims or proposing paid delivery.
For a local read-only scan, use app/readiness-web/README.md.
Child entrypoints: skills/geo-discover/SKILL.md, skills/geo-content/SKILL.md, skills/geo-measure/SKILL.md, skills/seo-plan/SKILL.md, skills/geo-optimize/SKILL.md, skills/webmcp-enable/SKILL.md.
-->

## 一份合格的结果包含什么

- 可发现、可理解、可操作三轴的独立状态；
- 对应的公开证据网址或仓库路径；
- 失败、受阻和未知的检查项；
- 唯一负责下一步的子 Skill；
- 验证命令、外部读回、未完成关口和必要的回滚方式；
- `ai_visibility` 与 `business_outcome` 的真实状态。

`agent_journey` 只记录一个公开路径能否进入、看懂并继续下一步。它是辅助证据，不参与三轴评分，也不能证明 AI visibility 或 business outcome。

需要可移交的机器可读报告时，使用 [readiness-report.json 模板](templates/readiness-report.json)。

## 从哪里使用

- 公网诊断站：https://readiness.bflabs.cn
- SkillHub：https://skillhub.cn/skills/user_49f8ec71/bflabs-agent-readiness
- Agent Skills 索引：https://readiness.bflabs.cn/.well-known/agent-skills/index.json
- MCP：https://readiness.bflabs.cn/mcp
- BFLabs Skills 目录：https://skills.bflabs.cn/catalog.html#geo
- CLI：

```bash
bflabs-readiness scan https://example.com --format markdown
```

网页、CLI、Markdown 和 MCP 使用同一份三轴报告合同。CLI 默认不会把网站发布到公开榜单；只有显式添加 `--publish-to-leaderboard` 才会申请公开。

## 公开榜单

榜单完全自愿，默认关闭。只有用户主动选择时，才会展示域名、三轴摘要、扫描时间和指纹；不会公开证据正文、Agent 提示词、IP 地址、AI visibility 或 business outcome。不想出现可以一直不上榜，已经加入也可以发送邮件到 hello@bflabs.cn 请求移除。

## 复测和交付边界

复测只读取扫描当时公开可见的网站。仓库改了但没有上线，复测不会当成已经更新；BFLabs 也不负责替用户证明网站曾经改过。Before / After 只比较两次公开网站状态。

免费层提供诊断、Agent 提示词、六个公开子 Skill 和复测。`geo-measure` 只汇总用户已经提供的观察。BFLabs 收费服务负责真实多平台抽样、跨系统实施、持续验证，以及客户授权后的业务结果归因。需要完整交付时，请联系 hello@bflabs.cn。
