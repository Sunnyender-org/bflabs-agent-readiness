---
half_life: 7d
archive_at: 2026-09-30
artifact_mode: ai-implementable-prd
scope_type: roadmap
scope_name: BFLabs Agent Readiness v1 complete refactor
coverage: Complete repository architecture, capability taxonomy, protocols, phased delivery, verification, packaging, and open-source release plan
not_complete_for: Public scanner deployment, customer production mutations, live third-party platform sampling, analytics attribution, and paid-service operations
verification_level: docs-only
real_smoke_status: not_required
review_status: reviewed
reviewer: codex
review_command: python3 ~/.agents/skills/delivery-planner/scripts/check_delivery_doc.py docs/agent-readiness-v1-complete-refactor-plan.md
review_notes: Plan checked against the current repository, existing product boundary, current root and child Skills, diagnostic app, and referenced public GEO repositories.
review_owner: Ender
review_due: 2026-08-18
execution_backend: docs-only
lead_agent: current
peer_agents: none
builder_agent: none
verifier_agent: none
verification_independence: self_checked
cwf_decision: not_needed
cwf_trigger_boundary: none
goal_handoff: orchestrator-goal
acceptance_contract_status: owner-confirmed
memory_required: true
memory_space: default
acceptance_memory_id: 177a2f65-9610-44c9-97d8-33a96562c0b8
memory_asserted_by: human:ender
memory_confirmed_by: human:ender
memory_intended_for: bflabs-agent-readiness maintainers and implementing agents
memory_validity: current
memory_valid_from: 2026-08-11
memory_review_due: event:phase-4-gate
---

# BFLabs Agent Readiness v1 完整改造计划

当前阶段、验证回执和下一切片由 [agent-readiness-v1-progress.md](agent-readiness-v1-progress.md) 维护；本文件继续作为产品边界和验收真源。

## 1. Alignment Snapshot

- **Building**：把现有单仓库升级为一个可注册、可路由、可编排、可验证、可打包的 GEO/SEO/Agent Readiness Skill Hub，同时保留诊断网站和两个现有子 Skill。
- **Not building**：不新建 `bflabs-geo-readiness` 平级产品；不开源真实平台账号采集器、客户生产变更、分析归因或收入证明；不做自动发布和内容农场。
- **Source of truth**：当前仓库代码与测试、根 `SKILL.md`、`references/product-boundary.md`、`references/routing.md`，以及本计划通过后形成的 v1 schemas 和 registry。
- **Audience**：网站所有者、GEO/SEO 服务团队、AI-native 产品团队、使用 Codex/Claude 等 Agent 优化网站的开发者。
- **Completeness**：对仓库完整改造和 v1 开源发布路径负责；不代表商业 SaaS、生产扫描服务或外部平台采样已经交付。
- **Verification level**：每个阶段至少通过 fixture/local；真实浏览器、Cloudflare、AI 平台或生产站点只在获得相应授权后提供 real-smoke 证据。
- **Forbidden writes**：本计划不授权 push、deploy、Cloudflare 修改、搜索平台提交、第三方发布、真实平台登录、客户站点修改或数据采集。
- **Open decisions**：没有阻塞规划的产品决策。默认继续使用 MIT；GEOHub 的 AGPL 实现只作为架构研究，不复制代码、Schema、模板或大段文字。

一句话能力：**输入一条中英文网站 GEO/SEO 请求或一个公开网站，BFLabs Agent Readiness 选择最小能力，产出有证据、可验证、可移交的诊断、机会、内容、测量或实施计划。**

## 2. Conservative Defaults

| Decision | Default | Why safe | Signal to revisit |
|---|---|---|---|
| Repository | 继续使用单一 `bflabs-agent-readiness` monorepo | 与现有对外叙事和安装入口兼容 | 子项目出现独立用户、版本和发布周期 |
| License | MIT；只独立实现外部 AGPL 项目的公开思想 | 保持既定开源策略并降低许可污染风险 | Ender 明确选择其他许可或取得单独授权 |
| Runtime | Python CLI/package + 现有 Node 诊断 app | 复用当前资产，避免引入 Web framework | 公网 SaaS 的规模与安全要求确定后 |
| Storage | 本地原子 run 目录，不默认上传 | 隐私、可重放、无需账号 | 商业托管和数据保留合同确定后 |
| Routing | 单意图最小 Skill；只有显式多阶段才运行 workflow | 防止隐式扩大任务和权限 | 新 workflow 通过独立契约和 eval 后 |
| Content | 先做价格、对比、页面蓝图和已有内容优化 | 对齐 BeefAPI 已观察到的转化问题 | 新内容模式获得真实需求和证据后 |
| Measurement | 只聚合用户提供的观测 | 不伪装真实平台采集 | 商业 adapter 获得合法技术路径和授权后 |

## 3. Product Positioning

### 3.1 产品定位

本仓库不是“保证 AI 推荐”的工具，也不是批量文章生成器。它是网站面向 AI 搜索与浏览器 Agent 的准备度操作系统：

```text
发现问题/机会
      |
      v
诊断 Discoverable / Understandable / Actionable
      |
      +----> 生成有证据的页面或内容方案
      |
      +----> 执行授权范围内的仓库本地优化
      |
      v
确定性验证 + 外部测量回执
```

### 3.2 核心差异化

1. 继续使用“可发现、可理解、可操作”三轴，WebMCP 只影响 Actionable，不混入 GEO 收录分。
2. 价格、模型、可用性等动态事实必须连接 canonical source，并携带版本或抓取时间。
3. 所有发现、建议和内容声明进入证据账本；缺证据时保留 `unknown`，不自动补写事实。
4. 开源层能诊断、规划、生成蓝图和验证；商业层负责真实平台重复采样、跨系统实施、监测和归因。
5. BeefAPI 案例提供真实的价格页、结构化价格接口、答案页、MCP/WebMCP 和外部可见度样本，但案例不自动推广为普遍因果结论。

### 3.3 目标用户与核心任务

| 用户 | 核心任务 | 开源交付 |
|---|---|---|
| 产品/官网负责人 | 判断网站为什么不被 AI 找到、读懂或调用 | 三轴证据报告、修复优先级 |
| GEO/SEO 运营 | 找到用户会向 AI 提出的高价值问题 | query map、opportunity map |
| 内容工程人员 | 把已确认事实组织成 AI 友好页面 | content spec、页面蓝图、改写稿 |
| 开发者/Agent | 在仓库内实施并验证优化 | Skill SOP、CLI、schemas、receipts |
| 服务团队 | 将诊断升级为客户交付 | 明确升级项与授权关口 |

## 4. Scope And Boundaries

### 4.1 开源层

- 本地公开网站扫描与三轴诊断；
- 仓库本地 GEO 优化和验证；
- 问题/意图/机会发现；
- 有证据的内容规格、页面蓝图和有限改写；
- 用户提供样本的离线测量与统计；
- SEO 范围识别与只读实施计划；
- MCP/WebMCP 审计、本地实现指导和验证合同；
- 注册表、路由、工作流、统一产物协议、CLI、eval、测试和打包。

### 4.2 商业交付层

- ChatGPT、Gemini、元宝、豆包、DeepSeek 等真实平台的重复联网抽样；
- 客户仓库、CMS、Cloudflare、Search Console/Bing 等跨系统实施；
- 周期监测、告警、证据保留与趋势分析；
- 客户授权的访问、转化和收入归因；
- 定制知识库、规模化内容运营与发布流程；
- 安全审查后的公网扫描服务。

### 4.3 永久禁止的暗示

- 准备度等于收录、引用、推荐、排名、转化或收入；
- 单次模型回答代表平台稳定表现；
- 离线观测聚合等于真实平台采集；
- Schema、`llms.txt`、FAQ 或 WebMCP 的存在本身保证效果；
- 未知产品事实可以由模型合理补全；
- 未授权即可修改生产、登录账号或代表用户对外发布。

## 5. UI Or Workflow Structure And Target Repository Shape

```text
bflabs-agent-readiness/
├── SKILL.md                         # 对 Agent 的统一自然语言入口
├── README.md
├── pyproject.toml                   # Python CLI/package
├── agents/
│   └── openai.yaml
├── registry/
│   ├── capabilities.json            # 能力、状态、入口、产物、权限
│   ├── workflows.json               # 仅两个稳定 DAG
│   └── research-evidence.json       # 规则与研究来源映射
├── schemas/
│   ├── capability.schema.json
│   ├── route-decision.schema.json
│   ├── run-manifest.schema.json
│   ├── evidence-ledger.schema.json
│   ├── quality-report.schema.json
│   ├── research-context.schema.json
│   ├── readiness-report.schema.json
│   ├── query-map.schema.json
│   ├── opportunity-map.schema.json
│   ├── content-spec.schema.json
│   ├── measurement-report.schema.json
│   └── seo-plan.schema.json
├── src/bflabs_readiness/
│   ├── cli.py                       # list/read/route/run/validate/package
│   ├── registry.py                  # registry 深模块
│   ├── router.py                    # 中英文最小能力选择
│   ├── orchestrator.py              # 显式多阶段工作流
│   ├── artifacts.py                 # 原子产物发布与 manifest
│   ├── evidence.py                  # 证据标准化与 claim linkage
│   ├── quality.py                   # schema/证据/降级质量门
│   └── providers/                   # 各子 Skill 的确定性 adapter
├── skills/
│   ├── geo-discover/
│   ├── geo-optimize/
│   ├── geo-content/
│   ├── geo-measure/
│   ├── seo-plan/
│   └── webmcp-enable/
├── workflows/
│   ├── discover-diagnose.md
│   └── discover-content.md
├── app/readiness-web/               # 统一产品的诊断前端，不是第三产品
├── runs/                             # gitignored 本地产物
├── examples/                         # 去隐私、可复现示例
├── evals/
│   ├── router_cases.json
│   ├── workflow_cases.json
│   ├── output_cases.json
│   └── forbidden_claim_cases.json
├── references/
│   ├── product-boundary.md
│   ├── routing.md
│   ├── measurement-boundary.md
│   ├── research-method.md
│   └── licensing-and-attribution.md
├── scripts/
│   ├── check_repository.py
│   ├── run_evals.py
│   ├── package.py
│   └── verify_packages.py
└── tests/
    ├── fixtures/
    ├── test_registry.py
    ├── test_router.py
    ├── test_workflows.py
    ├── test_artifacts.py
    ├── test_schemas.py
    └── test_packaging.py
```

## 6. Core Modules And Seams

### 6.1 Registry Module

**Interface**

```python
registry.list_capabilities(status=None) -> list[Capability]
registry.resolve(capability_id) -> Capability
registry.validate() -> ValidationReport
```

**Implementation responsibility**

- 读取和验证 capability/workflow registry；
- 拒绝未知、planned 或禁用入口被执行；
- 统一暴露 Skill 入口、输入 schema、输出 artifact、权限和降级策略；
- 替换当前 `scripts/skill_registry.py` 中的硬编码 `SKILLS` 字典。

删除该 Module 后，能力状态、路径安全和 schema 规则会散落到 CLI、根 Skill、测试和打包脚本，因此它应成为深模块。

### 6.2 Router Module

**Interface**

```python
router.route(text: str, context: RouteContext | None = None) -> RouteDecision
```

**Routing order**

1. 识别拒绝/越界意图；
2. 识别用户明确点名的子 Skill；
3. 识别明确的多阶段动词和顺序；
4. 单一意图选择最小 active capability；
5. 证据不足或多义时返回 `needs_clarification`，不猜测执行链。

CLI 的路由器使用可复现规则和 eval；根 `SKILL.md` 允许宿主 Agent 做语义理解，但输出必须符合同一 `route-decision` schema。不得把外部 LLM 设为仓库运行依赖。

### 6.3 Orchestrator Module

**Interface**

```python
orchestrator.run(route: RouteDecision, request: RunRequest) -> RunReceipt
```

仅支持两个稳定工作流：

```text
discover-diagnose: geo-discover -> geo-optimize(Audit)
discover-content:  geo-discover -> geo-content
```

单一意图不得自动升级为工作流。任何未来 workflow 先以 planned 状态进入 registry，通过独立输入/输出契约和 eval 后才能 active。

### 6.4 Artifact Module

**Interface**

```python
artifacts.publish(run_input, provider_outputs, evidence, quality) -> RunManifest
artifacts.validate(run_dir) -> ValidationReport
```

写入临时目录，所有 schema、哈希、引用和必需文件通过后再原子重命名为最终 run 目录。失败运行不得伪装成成功产物；保留结构化失败回执但不发布不完整 manifest。

### 6.5 Evidence And Quality Modules

**Evidence interface**

```python
evidence.record(source, capture, scope) -> EvidenceItem
evidence.link(claim_id, evidence_ids, support_level) -> ClaimSupport
```

**Quality interface**

```python
quality.evaluate(run_dir) -> QualityReport
```

质量门至少检查：schema、必需产物、证据链接完整性、未知状态保留、动态事实时间/版本、禁止声明、来源许可和可重放信息。

### 6.6 External Adapters

| Seam | 开源 adapter | 商业 adapter |
|---|---|---|
| Website evidence | 固定公开路径、本地快照 | 安全公网扫描器、授权 crawl |
| Platform observation | 用户导入 JSONL/CSV | 真实 AI 平台重复采样 |
| Analytics outcome | `not_measured` | 授权 analytics/订单/收入 |
| Website mutation | 仓库本地变更建议或实现 | CMS、Cloudflare、生产部署 |

只有当开源 adapter 与商业 adapter 都真实存在时才把 seam 抽成正式 port；在此之前保持内部接口，避免为假想扩展增加浅层抽象。

## 7. Unified Capability Registry

### 7.1 Capability Contract

```json
{
  "id": "geo-discover",
  "version": "1.0.0",
  "status": "active",
  "intents": ["discover", "compare", "evaluate", "act"],
  "languages": ["zh-CN", "en"],
  "entrypoint": "skills/geo-discover/SKILL.md",
  "execution": "offline",
  "input_schema": "schemas/discovery-brief.schema.json",
  "outputs": ["query-map", "opportunity-map", "evidence-ledger"],
  "permissions": ["read-local", "read-explicit-public-url"],
  "external_gates": [],
  "degrades_to": "bounded-plan"
}
```

Required invariants:

- `id + version` 唯一；
- `active` 必须有真实入口、输入 schema、输出 schema、正/负/近邻 eval；
- `planned` 不得有可执行 entrypoint；
- 权限缺失时降级或停止，不静默扩大授权；
- registry 只能暴露 allowlist 中的公开文件；`.receipts`、客户输入和 `runs` 永不进入发行包。

### 7.2 State List And v1 Capability Set

Registry 状态清单：`active` 可执行；`planned` 只返回可用性和最近替代能力；`disabled` 说明禁用原因；`deprecated` 在兼容窗口内可执行并发出迁移提示。

| Capability | v1 状态 | 单一职责 | 主要产物 |
|---|---|---|---|
| `bflabs-agent-readiness` | active | 统一入口和路由 | route decision / run receipt |
| `geo-discover` | active | 问题、意图和机会发现 | query map / opportunity map |
| `geo-optimize` | active | 品牌、网站、页面三轴诊断与仓库本地优化 | readiness report / repair receipt |
| `geo-content` | active | 从已确认事实生成有限内容产物 | content spec / Markdown / evidence units |
| `geo-measure` | active | 聚合用户提供的外部观测 | measurement report |
| `seo-plan` | active | SEO 范围识别和证据化行动计划 | SEO plan / evidence gaps |
| `webmcp-enable` | active | Agent Actionability 实现与验证 | task plan / verification receipt |

## 8. Task Coverage

### 8.1 14 类 GEO 能力

| 类别 | Route | 交付边界 |
|---|---|---|
| GEO 问题了解 | `geo-discover` | 基于种子、受众、场景生成问题簇 |
| GEO 机会比较 | `geo-discover` | 比较意图、页面覆盖和证据缺口，不编造流量 |
| GEO 准备度评估 | `geo-optimize:Audit` | 三轴诊断与证据 |
| GEO 行动建议 | `geo-optimize:Audit` | P0/P1/P2 修复计划 |
| 品牌诊断 | `geo-optimize:Audit` | 实体、产品定位、事实一致性 |
| 网站诊断 | `geo-optimize:Audit` | 公开入口、robots、sitemap、协议、工具 |
| 页面诊断 | `geo-optimize:Audit` | 可抽取性、证据、动态事实和转化路径 |
| 标题 | `geo-content:title` | 不夸大事实的标题方案 |
| 科普解释 | `geo-content:explainer` | 定义、限制、证据和操作步骤 |
| 对比 | `geo-content:comparison` | 对称维度、事实来源、未知项 |
| 榜单 | `geo-content:ranking` | 必须有明确入选规则和数据，不支持伪榜单 |
| 页面蓝图 | `geo-content:page-blueprint` | 页面结构、组件、schema 和 canonical facts |
| 内容优化 | `geo-content:refine` | 保留原意与证据的局部优化 |
| AI 友好改写 | `geo-content:article-friendly` | 增强结构和事实密度，不保证被引用 |

网站 SEO 规划由独立统一入口 `seo-plan` 承担，不挤进 14 类 GEO 能力，也不自动变成实施。

### 8.2 首发内容优先级

虽然协议覆盖七种模式，首发实现顺序必须依据 BeefAPI 已出现的真实转化信号：

1. `page-blueprint`：模型价格答案页；
2. `comparison`：模型/渠道/分组价格对比；
3. `refine`：现有价格和接入页面优化；
4. `article-friendly`：把已有事实页改成可抽取结构；
5. `title`、`explainer`；
6. `ranking` 最后实现，并设置最严格证据门。

## 9. Unified Artifact Protocol 1.0

每次成功执行生成：

```text
runs/run-{utc}-{short-id}/
├── input/request.json
├── route-decision.json
├── evidence-ledger.json
├── quality-report.json
├── run-manifest.json
├── research-context.json            # 仅研究规则适用时
└── outputs/{provider-artifacts}
```

### 9.1 Run Manifest

必须记录：protocol version、run id、capability/version、workflow id、created time、input hash、artifact path/hash/media type/schema、status、degradation、external gates 和 replay command。

### 9.2 Evidence Ledger

证据项至少包含：

- `evidence_id`；
- 来源类型：repository/public-url/user-supplied-observation/research；
- canonical locator；
- captured_at；
- content hash 或版本；
- 支持范围与限制；
- 许可/署名信息；
- 是否包含动态事实。

声明必须列出 `claim_id`、支持证据、支持等级 `direct|derived|context-only|unsupported`。`unsupported` 声明不得进入最终内容正文。

### 9.3 Quality Report

质量状态：`pass|pass_with_warnings|blocked|failed`。至少包含：

- schema validation；
- artifact completeness；
- claim-evidence coverage；
- unknown preservation；
- dynamic fact freshness；
- forbidden claim scan；
- privacy and packaging scan；
- replay readiness。

### 9.4 Measurement Report

只接收用户提供的观测文件。每个指标必须同时报告分子、分母、排除数、缺失数、平台/终端分层和捕获时间。首发指标：

- 联网率；
- 站点引用率；
- 内容吸收率；
- 品牌出现率；
- 推荐率；
- 动态事实正确率。

不得从普通网页搜索结果构造“模型回答”，不得把没有联网证据的回答计入联网样本。

## 10. Research Kernel

### 10.1 目的

研究库不进入关键运行依赖。它只负责把规则与来源、适用平台、样本范围、因果状态、代理变量和限制绑定，防止“54 篇论文”变成无法审计的宣传数字。

### 10.2 首批原则

1. 引用选择与内容吸收分开测量；
2. Web 与 App 样本分层；
3. 描述性相关不升级为因果结论；
4. Q&A 形式不是独立加分项；
5. 内容匹配、结构清晰和证据密度只在适用样本范围内作为诊断信号；
6. 动态事实需要 canonical source 和 freshness；
7. 排名、流量、转化和收入需要独立数据。

### 10.3 来源与许可

- GEO Citation Lab 的代码/Skill 可按 MIT 使用并保留声明；自有报告和可视化按 CC BY 4.0 署名；第三方论文和数据遵守各自许可。
- qiaomu-seo、yao-geo-skills 和 Waza 的可复制内容仅在保留相应 MIT 声明时使用。
- GEOHub 的 AGPL 代码、Schema、模板、测试和正文不得复制进本 MIT 仓库；只允许基于公开思想进行独立实现，并在 references 中说明启发来源。

## 11. CLI Contract

目标入口：

```bash
bflabs-readiness list [--status active] [--format json|markdown]
bflabs-readiness read {capability-id}
bflabs-readiness route --text "{中英文请求}" [--format json]
bflabs-readiness run --text "{请求}" --input brief.json --output runs/
bflabs-readiness run --capability {id} --input brief.json --output runs/
bflabs-readiness validate [--run {run-dir}]
bflabs-readiness eval
bflabs-readiness package --target source|unified|{capability-id}
```

Compatibility:

- 现有 `python3 scripts/skill_registry.py list|read|validate` 在 v1 保留为 deprecated wrapper；
- 连续两个 minor release 后才能移除 wrapper；
- 现有 `templates/readiness-report.json` 升级为正式 schema/example，不直接删除；
- `geo-optimize` 和 `webmcp-enable` 的现有调用保持可用。

## 12. Diagnostic Web App Retrofit

诊断网站仍是统一产品的一个 app，不拆仓库。首发页面结构：

```text
+-----------------------------------------------------------+
| 输入公开域名                               [开始诊断]      |
+-----------------------------------------------------------+
| 三轴摘要：Discoverable | Understandable | Actionable      |
+-----------------------------------------------------------+
| 证据与失败谓词 | 机会问题 | 推荐修复 | 可用子 Skill       |
+-----------------------------------------------------------+
| 未测量：AI visibility / Business outcome                  |
| [下载 Artifact Pack] [复制 Agent 优化指令] [联系 BFLabs] |
+-----------------------------------------------------------+
```

P0 保持固定公开路径扫描，不扩张为全站 crawler。Web app 通过 Artifact Protocol 输出报告，不维护第二套评分结构。内容生产和测量先通过 CLI/Skill 使用，网页只展示路由建议；等协议稳定后再增加导入样本和生成 blueprint 的 UI。

公网部署仍单列生产安全项目，需要 DNS pinning/rebinding 防护、目标/客户端限流、滥用控制、opt-out、保留策略、隐私说明和独立安全审查。本路线图不把本地 smoke 当公网就绪证明。

## 13. Failure Paths And Degradation Behavior

**failure path 1 — 缺证据**：保持 `unknown` 或 `blocked`，返回取证清单，不生成事实正文。

**failure path 2 — 缺权限或外部能力**：降级为本地计划/离线回执，记录 external gate，不尝试登录、授权或生产变更。

| Failure | Required behavior |
|---|---|
| 意图多义 | 返回候选 route 和一条最小澄清问题，不自动串联多 Skill |
| capability 为 planned/disabled | 返回可用状态、所需输入和最近 active capability |
| canonical facts 缺失 | 阻止内容事实声明，允许输出缺口和采集清单 |
| 公网抓取失败 | 保留失败证据，允许用户提供本地快照，不把失败计作零分 |
| schema 不通过 | run 标记 failed，不原子发布成功 manifest |
| 动态价格过期 | 标记 stale，禁止写入“当前价格”正文 |
| 观测样本缺字段 | 排除并报告原因，不静默进入分母 |
| 外部权限缺失 | 降级为计划或本地验证，记录 external gate |
| unsupported browser/WebMCP | 保留直接 MCP/API 和人工页面 fallback |
| 禁止请求 | 解释边界并返回安全替代，不生成暗示保证的产物 |

## 14. Delivery Phases

### Phase 0 — Contract And License Baseline

**Deliverables**

- 本计划确认后转为 owner-confirmed；
- 固化 capability taxonomy、open/commercial boundary 和 attribution 文件；
- 为当前报告和现有两个 Skill 建立 v1 compatibility fixtures；
- 增加禁止复制 AGPL 实现的 repo check。

**Verification**

- 现有全部检查继续通过；
- 旧示例可被新 compatibility fixture 读取；
- repository scan 不包含 GEOHub 派生代码或未声明的大段复制内容。

**Stop condition**：产品边界、许可证或 Skill 数量被重新定义时暂停后续阶段并更新本计划。

### Phase 1 — Registry, Schemas And Artifact Kernel

**Vertical slice**：用新 CLI 执行现有 `geo-optimize:Audit` fixture，并产生完整 Artifact Protocol run。

**Deliverables**

- `pyproject.toml` 和 `src/bflabs_readiness`；
- registry、schema、artifact、evidence、quality Modules；
- `list/read/run/validate` CLI；
- 旧 CLI wrapper；
- schema、manifest hash、原子发布和路径 allowlist 测试。

**Verification**

- fixture 运行生成所有必需产物；
- 修改任何产物后 manifest 校验失败；
- `.receipts`、`runs`、私有绝对路径不会进入 package。

### Phase 2 — Bilingual Router And Stable Workflows

**Vertical slice**：中英文单意图分别路由到现有两个 Skill；显式“先发现再诊断”生成精确 DAG。

**Deliverables**

- route-decision schema；
- 中英文 router cases；
- forbidden、negative 和 near-neighbor cases；
- 两个 workflow registry 条目；
- planned/disabled 降级行为。

**Verification**

- 单意图只选择一个最小 Skill；
- 只有显式多阶段请求生成 DAG；
- 越界请求零误执行；
- router eval 达到第 17 节目标。

### Phase 3 — GEO Discover And Discover-Diagnose

**Vertical slice**：输入 BeefAPI“GPT-5.6 价格”种子和公开站点事实，输出问题地图，再调用 `geo-optimize:Audit` 形成诊断。

**Deliverables**

- `geo-discover` Skill、brief/schema、query map、opportunity map；
- 问题维度：受众、场景、比较、决策、价格/成本、接入、限制；
- 机会排序只使用覆盖、证据缺口、业务相关性等可解释字段，不伪造搜索量；
- `discover-diagnose` workflow。

**Verification**

- 每个机会可追溯到种子、输入事实或明确假设；
- 不提供搜索量时结果明确标记 `not_measured`；
- 工作流第二阶段只消费第一阶段 schema 输出。

### Phase 4 — GEO Content And Discover-Content

**Vertical slice**：从已验证 `pricing.json` 和模型页面生成“GPT-5.6 价格答案页”blueprint，再校验所有价格 claim 的 evidence linkage。

**Deliverables**

- `geo-content` Skill 和七种 mode contract；
- content brief、content spec、evidence units 和 Markdown 输出；
- 动态事实 freshness gate；
- 比较对称性、榜单方法披露、禁止编造 citation 检查；
- `discover-content` workflow。

**Verification**

- 所有事实 claim 有 direct/derived evidence；
- 修改 canonical price fixture 后旧输出被标记 stale；
- ranking 无数据或方法时必须 blocked；
- HTML 输出如启用，必须转义用户输入。

### Phase 5 — GEO Measure And Research Kernel

**Vertical slice**：导入一批已知答案的 ChatGPT/Gemini/国内平台 fixture，复算联网率、引用率、吸收率、品牌出现率、推荐率和价格正确率。

**Deliverables**

- observation 和 measurement report schemas；
- CSV/JSONL import adapters；
- 分子/分母/排除/缺失和平台终端分层；
- Wilson interval；
- research evidence registry/context；
- 研究原则与运行规则映射审计。

**Verification**

- fixture 指标与人工答案完全一致；
- 普通搜索结果不能作为模型回答导入；
- 无有效样本时如实输出零有效样本，而不是 0% 效果；
- 研究结论携带 causal status 和 limitation。

### Phase 6 — SEO Plan

**Vertical slice**：输入一次网站迁移/索引问题请求，输出只读证据清单、优先检查项、实施前置条件和回滚要求。

**Deliverables**

- `seo-plan` Skill、brief/schema、plan artifact；
- robots 与 meta/X-Robots、canonical、sitemap/IndexNow、structured data、CWV lab/field、AI crawler 区分；
- Google/Bing/OpenAI/Microsoft 等官方来源 freshness registry；
- 不进行 live Search Console、CMS mutation 或排名查询。

**Verification**

- 无站点证据时只产出 scope/evidence gaps，不产出伪 finding；
- 技术建议链接到当前官方来源；
- implementation actions 标明授权和 rollback gate。

### Phase 7 — Web App Protocol Integration

**Vertical slice**：本地扫描 BeefAPI fixture/站点，网页与 CLI 对同一证据生成 schema 等价报告并可下载 Artifact Pack。

**Deliverables**

- scanner 输出迁移至 shared readiness schema；
- UI 展示 failed predicates、机会入口、子 Skill 路由和 BFLabs 联系方式；
- “复制 Agent 优化指令”和 Artifact Pack 下载；
- 旧 API response 兼容层；
- UI 可访问性和移动端回归。

**Verification**

- CLI/UI 相同 fixture 的 axis/check ids 一致；
- 屏幕阅读器标签、键盘操作和 360px 宽度可用；
- SSRF 和 redirect safety 测试继续通过；
- 不显示神秘总分，不混淆 AI visibility/business outcome。

### Phase 8 — Packaging, Docs And Public Release Candidate

**Deliverables**

- source、unified 和六个子 Skill package；
- Codex/Claude 安装说明；
- isolated install simulation；
- BeefAPI 去隐私案例和完整示例 Artifact Pack；
- architecture、protocol、contribution、security、attribution 文档；
- release checklist 和 changelog。

**Verification**

- 每个 package 只包含 allowlist 文件并可独立安装/读取；
- unified package 可以完成两个稳定 workflow；
- CI 从干净环境运行 tests、eval、package verify；
- 公开材料不包含真实 receipts、用户数据、绝对路径、令牌或内部运营信息。

**Release gate**：Ender 单独批准 commit/push/release；公网诊断站部署另走生产安全评审，不随 Skill release 自动发生。

## 15. Priorities

| Tier | Scope | Acceptance signal |
|---|---|---|
| P0 | Phase 0-2：内核、协议、注册表、路由、现有能力兼容 | 旧能力不回归，新 Artifact run 可重放 |
| P1 | Phase 3-4：发现、价格/对比内容、两个工作流 | BeefAPI 价格问题形成完整 discover→diagnose/content 闭环 |
| P2 | Phase 5-7：测量、研究、SEO、Web app 协议统一 | 离线样本复算正确，CLI/UI 使用同一事实模型 |
| P3 | Phase 8 和商业适配器 | 可安装发行包；真实外部动作分别获得授权和回执 |

## 16. Test And Eval Strategy

### 16.1 Test layers

| Layer | Test surface | 禁止替代的证据 |
|---|---|---|
| Unit | registry/router/evidence/quality 深模块 interface | 不证明真实网站或平台效果 |
| Contract | JSON Schema、capability input/output | 不证明外部集成 |
| Fixture | BeefAPI 和合成站点快照 | 不证明当前生产状态 |
| Local smoke | CLI、诊断 app、package install | 不证明公网安全或部署 |
| Real smoke | 经授权的公开站点、浏览器、AI 平台 | 仅证明该批次和范围 |
| Production | 外部服务读回、监控、回滚证据 | 单独发布关口 |

### 16.2 Required eval families

- 每个 capability：至少 8 positive、8 negative、8 near-neighbor；
- 根 router：中英文对称覆盖、显式 mode、显式 workflow、planned route、forbidden route；
- output cases：正常、缺证据、动态事实过期、部分失败、完全 blocked；
- fabrication cases：未知价格、客户、性能、排名、引用、推荐和收入；
- packaging cases：私有目录、绝对路径、symlink/path traversal、未声明许可证；
- compatibility cases：旧 CLI、旧 readiness report、现有两个 Skill 示例。

## 17. Performance Metrics And Quality Targets

| Metric | Target | Measurement | Degradation threshold |
|---|---:|---|---:|
| Router exact-route accuracy | ≥ 95% | 固定中英文 eval set | < 92% 阻止发布 |
| Forbidden request execution | 0 | forbidden cases | > 0 阻止发布 |
| Explicit workflow precision | 100% | workflow cases | < 100% 阻止发布 |
| Schema-valid successful runs | 100% | all output cases | < 100% 阻止发布 |
| Unsupported factual claims | 0 | claim-evidence checker | > 0 阻止发布 |
| Deterministic fixture runtime | p95 ≤ 2s | CI fixtures, excluding package install | p95 > 4s |
| Local public scan completion | p95 ≤ 30s | bounded six-path smoke | p95 > 45s |
| Package private-file leaks | 0 | package allowlist check | > 0 阻止发布 |
| Measurement arithmetic | 100% exact | golden fixtures | any mismatch blocks release |
| Existing skill compatibility | 100% | compatibility cases | any P0 regression blocks release |

## 18. Acceptance Matrix

| Criterion | Evidence level | Test or manual evidence | Status | Notes |
|---|---|---|---|---|
| 单仓库包含根入口、六个子 Skill 和诊断 app | local | registry list + repository check | pending | 不新建平级 GEO 产品仓库 |
| 单意图进入最小可用 Skill | fixture | router eval | pending | 中英文覆盖 |
| 仅两条显式稳定 workflow 可执行 | fixture | workflow eval | pending | 单意图不自动编排 |
| 所有成功 run 使用统一 Artifact Protocol | fixture | schema/manifest tests | pending | 原子发布 |
| 每个事实 claim 可追溯证据 | fixture | evidence coverage test | pending | unsupported 不得进入正文 |
| 三轴准备度保持独立 | local | scanner/CLI compatibility test | pending | WebMCP 不进入 GEO 分数 |
| AI visibility 和 business outcome 默认未测量 | fixture | forbidden claim cases | pending | 独立证据才能改变状态 |
| 七种内容模式共享证据和质量合同 | fixture | output cases | pending | ranking 需要严格方法门 |
| 测量报告保留分母、排除和平台/终端分层 | fixture | golden measurement tests | pending | 离线聚合不伪装采集 |
| SEO 入口只产出有边界的计划 | fixture | SEO output tests | pending | 不自动登录或修改 |
| 旧 CLI、旧报告和两个现有 Skill 不回归 | local | compatibility suite | pending | wrapper 有移除窗口 |
| MIT 包无 AGPL 派生实现和私有内容 | local | license/package scan + human review | pending | 启发来源正常署名 |
| 统一包和各子包均可隔离安装验证 | local | package install simulation | pending | 干净临时环境 |
| 公开 release 由独立动作关口批准 | docs-only | release checklist | pending | 计划完成不等于 push/release |

## 19. Developer Handoff

### Build first

只实现 Phase 0-1 的纵向 slice：让现有 `geo-optimize:Audit` fixture 经 registry 和 CLI 运行，产出一套通过 schema/manifest/evidence/quality 校验的 Artifact Protocol run。不要先创建所有空 Skill 目录。

### Do not reinterpret

- 产品始终是 `bflabs-agent-readiness` 单仓库；
- 三轴评分和 AI visibility/business outcome 分离；
- 真实平台采样、生产实施和归因属于商业 adapter；
- GEOHub 代码是 AGPL，不进入本 MIT 实现；
- 单意图最小路由，多阶段只有两个明确 workflow；
- unknown/blocked 不得被转换成低分或事实；
- 现有用户改动、receipts 和私有内容不可被打包或覆盖。

### Flexible choices

- Python 内部文件拆分和数据类实现；
- JSON Schema 校验库的具体选择，但应保持依赖最小且锁定兼容范围；
- CLI 输出美化方式；
- run id 具体格式；
- compatibility wrapper 的内部实现。

### Known unknowns

- 公网诊断 app 的最终托管环境和滥用控制实现；
- 商业平台采样 adapter 的合法登录/自动化方式；
- 客户分析和收入归因的数据接口；
- 是否提供独立商业许可证或托管版本。

这些未知项不阻塞开源 v1 内核，也不得由实现 Agent 自行决定。

### Pause conditions

- 需要复制 AGPL 内容才能继续；
- registry 和 Artifact Protocol 无法兼容现有两个 Skill；
- 新依赖引入不可接受的安装或安全负担；
- 需要改变公开产品定位、MIT 许可或商业/开源边界；
- 需要真实账号、凭据、生产变更、对外发布或付费资源。

## 20. Goal Handoff Decision

- `goal_handoff`: `next-stage-goal`
- `produced_goal`: 本计划由 Ender 确认后，另行生成只覆盖 Phase 0-1 的实施 Goal；不把八个阶段一次性交给无界执行任务。
- `shape_reason`: 完整改造跨多个可独立验收版本，使用父路线图加当前阶段 Goal 比单一巨大 Goal 更可控。
- `evidence_before_next_goal`: 本计划 owner confirmation、干净 worktree、现有 tests baseline、Phase 0-1 acceptance slice。

## 21. Execution Backend Decision

- `execution_backend`: 当前为 `docs-only`；实施阶段默认 `direct` 或 `skill-only`。
- `cwf_decision`: `not_needed`。
- `cwf_trigger_boundary`: `none`。
- `backend_reason`: 计划编写不需要多 Agent 编排；每个实施阶段可由一个 Builder 完成并运行本地检查。
- `if_cwf`: 仅在后续明确要求独立 Builder/Verifier、仓库级并行审计或长时间可恢复执行时启用。
- `if_not_cwf`: 使用一个阶段 Goal、一个主实现者、阶段结束时按 acceptance matrix 验证。
