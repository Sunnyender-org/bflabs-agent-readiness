# BFLabs Agent Readiness v1 Progress

更新时间：2026-08-17

```text
进度罗盘：BFLabs Agent Readiness v1 complete refactor
位置：v1 Draft PR 后续 / 产品试用闭环与 Cloudflare Worker 发布候选完成
状态：本地产品闭环可演示；公网 Worker 安全边界与 dry-run 已验证；尚未 commit、push、merge、release 或 deploy
本轮：补齐 Artifact Pack + Agent 指令交接、同站 Before / After、真实询盘入口、免费/付费边界，以及 strictly-public fetch、双限流、opt-out、无应用数据库留存的 Worker 入口
下一关口：按 Ender 2026-08-17 的明确批准 commit/push，等待 CI 后 merge、release，并部署到不覆盖官网的 `readiness.bflabs.cn`
```

## Verified State

```yaml
verified_state:
  maker_state: changed
  checker_state: passed
  checker: Codex self-check plus deterministic tests
  verification_receipt: this document
  authoritative_state_artifact: docs/agent-readiness-v1-progress.md
```

这不是独立 Verifier 结论，也不是 release 证明。v1 commit `8bd65d4` 已 push 并形成 Draft PR #1；2026-08-17 的产品化与 Worker 改动仍在本地工作树，未 commit、未 push、未 deploy。

## Phase 0 — Contract And License Baseline

状态：`pass`

已完成：

- owner-confirmed 路线图、总控 Goal 和独立进度投影；
- 七项 capability taxonomy，其中根入口、`geo-optimize`、`webmcp-enable` active，其余按阶段保持 planned；
- MIT 根许可、第三方 notices、GEOHub clean-room 规则与 package license gate；
- 现有 `geo-optimize` receipt 的兼容 fixture；
- repository checker 排除 `node_modules`、`.venv`、`build`、`dist`、`runs` 和私有 receipts，修复既有误扫问题。

验收证据：

- `python3 scripts/check_repository.py`：pass，7 capabilities；
- `skills/geo-optimize/scripts/check_package.py`：pass，5 positive / 5 negative；
- `skills/webmcp-enable/scripts/check_package.py`：pass，4 positive / 4 negative；
- 人工 diff/provenance 检查：新增运行实现由本路线图独立设计，未引入 GEOHub 源码、schemas、templates、tests 或正文。

## Phase 1 — Registry, Schemas And Artifact Kernel

状态：`pass`

已完成：

- Python package、`bflabs-readiness` CLI 和 installed share data；
- Registry、Schema、Artifact、Evidence、Quality 深模块；
- `list`、`read`、`run`、`validate`；
- 旧 `scripts/skill_registry.py` 兼容 wrapper；
- `geo-optimize` receipt 到 Artifact Protocol 1.0 的纵向 adapter；
- 原子 run、manifest/hash/schema 校验、证据链接、动态事实版本门、测量边界和禁止声明检查；
- 源码优先级与 installed share fallback，避免当前 worktree 被旧 wheel 快照遮蔽。

端到端产物：

```text
run-*/
├── input/request.json
├── evidence-ledger.json
├── quality-report.json
├── run-manifest.json
└── outputs/readiness-report.json
```

验收证据：

- `python -m unittest discover -s tests`：13 tests pass；
- `python scripts/skill_registry.py validate`：repository、两个子 Skill 和 13 tests 全部 pass；
- `npm test --prefix app/readiness-web`：6 tests pass；
- `npm run check --prefix app/readiness-web`：pass；
- `bflabs-readiness validate --run {run-dir}`：pass；
- wheel 在仓库外 cwd 完成 `list`、`read`、`validate`、`run` 和 run re-validation；
- wheel：33,757 bytes，SHA-256 `5d469593a7240b77c405818c13fb5637f8945c3ad7e069dd14ff3ed855e82b70`；
- wheel allowlist 检查：34 files、required assets complete、0 private path/receipt leaks。

质量门结果：

| Check | Result |
|---|---|
| evidence id uniqueness | pass |
| claim-evidence coverage | pass |
| dynamic fact freshness/version | pass |
| AI visibility/business outcome boundary | pass |
| forbidden outcome guarantees | pass |
| manifest artifact hashes | pass |
| input hash binding | pass |
| tamper detection | pass |
| blocked run atomic non-publication | pass |

## Phase 2 — Bilingual Router And Stable Workflows

状态：`pass`

已完成：

- `route-decision` JSON Schema；
- `bflabs-readiness route --text` 中英文统一入口；
- 单一意图选择一个最小 capability；
- 只有显式“发现后诊断”与“发现后内容生产”请求生成 DAG；
- planned capability/workflow 返回 non-executable、reason 和 active fallback；
- guarantee、bulk publishing、admin exposure、auth bypass 和 autonomous payment 明确 rejected；
- 固定 bilingual、forbidden、workflow、ambiguous 和 near-neighbor eval；
- current worktree 优先于已安装 share，wheel 离开源码目录后仍使用 packaged registry/schema。

验收证据：

- router eval：62/62，accuracy `1.0`；
- forbidden cases：8，misroutes `0`；
- workflow cases：8，precision `1.0`；
- Python tests：19 pass；
- wheel outside-cwd：active capability route、planned workflow DAG、forbidden rejection 和 registry validation 全部 pass；
- wheel：36 files，SHA-256 `005cdaa995ca3d12e5ff5d03dec60ec018850f04356a742aabd903f85ad93f1d`；
- package scan：route schema exactly once，0 private path/receipt leaks。

Phase 2 不把两个 workflow 标记为 executable：`geo-discover` 和 `geo-content` 尚为 planned，分别在 Phase 3 和 Phase 4 通过 provider 验收后再激活对应路径。

## Phase 3 — GEO Discover And Discover-Diagnose

状态：`pass`

已完成：

- `geo-discover` 子 Skill、discovery brief、query map 和 opportunity map schemas；
- 受众、场景、比较、决策、价格/成本、接入、限制七个固定维度；
- 每条 query 追溯到输入、种子或显式假设，每个 opportunity 追溯到 query；
- 机会分只由 coverage gap、evidence gap、business relevance 构成，搜索量保持 `not_measured`；
- `discover-diagnose` 激活并以一个原子 run 串联 discovery artifact 与 diagnosis evidence；
- `discover-content` 继续保持 planned。

验收证据：

- repository、三个子 Skill、router eval 和 Python tests 总门禁通过；
- Python tests：25 pass；router eval：62/62，workflow precision `1.0`；
- 直接 `geo-discover` 与 `discover-diagnose` run 均通过 schema/hash/replay validation；
- workflow receipt 明确记录 `opportunity-map -> ev_discovery_opportunity_map -> discovery-opportunity-coverage` 数据流；
- wheel 在仓库外 cwd 完成 list、route、两种 run 和 re-validation；
- wheel：50,215 bytes，44 files，SHA-256 `6b3cbfd869e252e6be8585b1804f6845de6588a590c124703e0c4f0742c0375f`；
- package scan：Phase 3 required assets complete，0 private path/receipt leaks。

## Phase 4 — GEO Content And Discover-Content

状态：`pass`

已完成：

- `geo-content` 子 Skill、content brief/spec/evidence units schemas 和真实 Markdown artifact；
- `title`、`explainer`、`comparison`、`ranking`、`page-blueprint`、`refine`、`article-friendly` 七种 mode contract；
- 每个事实 claim 只允许 `direct|derived` evidence linkage；
- 动态事实同时绑定 canonical evidence hash 和 `fact_version`，变更快照会阻止旧内容发布；
- 对比对称性、榜单方法与数据范围、refine/source preservation、内部 citation integrity、禁止结果承诺门；
- `discover-content` 激活并将 opportunity map 作为 content spec 的 `discovery_context`；
- Markdown 作为 `text/markdown; charset=utf-8` 进入 manifest hash 和 run re-validation；
- publication gate 固定为 `owner-approval-required`，未执行发布、部署或外部写入。

验收证据：

- repository、四个子 Skill、router eval、Python tests 和诊断 app 总门禁通过；
- Python tests：31 pass；router eval：62/62，workflow precision `1.0`；诊断 app：6 pass；
- 七种 mode 全部生成 schema-valid、evidence-linked Markdown；ranking 缺方法、comparison 不对称、动态价格 hash/version 失配均 blocked；
- 直接 `geo-content` 与 `discover-content` run 均通过 schema/hash/replay validation；
- workflow receipt 明确记录 `opportunity-map -> ev_discovery_opportunity_map -> content-spec.discovery_context` 数据流；
- wheel 在仓库外 cwd 完成 Skill read、route、两种 run 和 re-validation；
- wheel：92,461 bytes，80 files，SHA-256 `85e88435a22850f31f555bf2bd4edecf1ca93885ed79df554594a267b5fd459a`；
- package scan：Phase 4 schemas、Skill references/templates/examples complete，0 private path/receipt leaks，0 AGPL implementation markers。

## Phase 5 — GEO Measure And Research Kernel

状态：`pass`

已完成：

- `geo-measure` 子 Skill、observation、measurement input/report 和 research context schemas；
- JSON、JSONL、CSV 三种离线输入 adapter；
- 联网率、站点引用率、内容吸收率、品牌出现率、推荐率、动态事实正确率六项独立指标；
- 每项指标保留 numerator、denominator、excluded、missing、rate、denominator rule 和 95% Wilson interval；
- platform + terminal 分层，且每项指标满足 `denominator + excluded + missing = input`；
- 普通网页搜索结果和证据不完整样本不能进入有效模型回答分母；
- 无有效样本时 rate/interval 为 `null` 并发出 warning，不伪装成 `0%`；
- research evidence registry 绑定 statement、source、license、platform/sample scope、causal status、proxy、limitations 和 runtime rules；
- 研究规则保持描述性，不把 readiness 或回答观测升级为排名、流量、转化或收入结论；
- active `geo-measure` 仅做离线聚合，不要求或执行 platform sampling。

验收证据：

- repository、五个子 Skill、router eval 和 Python tests 总门禁通过；
- Python tests：36 pass；router eval：62/62，workflow precision `1.0`；
- 8 条已知 fixture 复算为 6 valid / 2 excluded，其中 1 条普通搜索结果和 1 条不完整证据被排除；
- overall 与 6 个 platform/terminal strata 通过 schema/hash/replay validation；
- JSONL/CSV adapters 与 JSON 观测结构等价；hash tamper blocked；零有效样本 `pass_with_warnings`；
- wheel 在仓库外 cwd 完成 Skill read、route、measurement run 和 re-validation，route 无虚假的 platform-sampling gate；
- wheel：107,189 bytes，93 files，SHA-256 `970ad16e9fb7cf00b00f50f0b0e6aeeeee74543f2478ddc85a43490e0e2bf926`；
- package scan：Phase 5 schemas、research registry、Skill references/templates complete，0 private path/receipt leaks，0 AGPL implementation markers。

## Phase 6 — SEO Plan

状态：`pass`

已完成：

- `seo-plan` 子 Skill、brief、plan 和 official source registry schemas；
- robots、meta/X-Robots、canonical、redirects、sitemap、IndexNow、structured data、CWV lab/field、AI crawler、hreflang 十一类独立检查；
- 无站点证据时只输出 scope、read-only checks 和 evidence gaps，不生成 finding 或 implementation action；
- 只有 evidence-linked `fail` observation 才生成 finding；
- 每项 implementation action 固定 `owner-approval-required`，并包含 preconditions 和 rollback；
- Google、Microsoft Bing、IndexNow、OpenAI 官方来源记录 URL、HTTP 200、captured_at、content hash、freshness days 和 limitations；
- 官方来源超出 freshness window 会阻止 plan publication；
- Search Console、Bing Webmaster Tools、CMS/server/DNS mutation 和 live ranking query 明确未执行。

验收证据：

- repository、六个子 Skill、router eval、Python tests 和诊断 app 总门禁通过；
- Python tests：41 pass；router eval：62/62，workflow precision `1.0`；诊断 app：6 pass；
- migration fixture 生成 4 个 evidence-linked findings、7 个 gaps、11 个 read-only checks 和 4 个 owner-gated rollback actions；
- no-evidence fixture 生成 11 gaps、0 findings、0 implementation actions，并以 `pass_with_warnings` 原子发布；
- stale official source 与无 evidence 的 failed observation 均 blocked；
- wheel 在仓库外 cwd 完成 Skill read、route、evidence/no-evidence 两种 run 和 re-validation；
- wheel：120,831 bytes，104 files，SHA-256 `ab26132927f80b08afbc06d89d1312c18aea2a3cd4d6400769b9ee1c759ffbc8`；
- package scan：SEO schemas、official source registry、Skill references/templates complete，0 private path/receipt leaks，0 AGPL implementation markers。

## Phase 7 — Web App Protocol Integration

状态：`pass`

已完成：

- scanner canonical `readiness_report` 迁移至共享 `readiness-report.schema.json`，旧 `axes`、evidence、scan 和 findings response 保留为兼容层；
- canonical report、evidence ledger、quality report 与 manifest 使用 Artifact Protocol 1.0.0，并由网页下载完整 Artifact Pack；
- 页面展示 failed predicates、evidence gaps、bounded opportunities、最小子 Skill 路由和 BFLabs 公共仓库联系入口；
- Agent 优化指令可复制，且明确保留 unknown、AI visibility/business outcome `not_measured` 和 Owner gate；
- 缺失抓取证据保持 unknown，相关轴不计分；WebMCP 缺证据保持 `unknown`，MCP server card 不再被误标为浏览器原生 WebMCP；
- 键盘焦点样式、表单 `aria-busy`、进度 live region、skip link、语义按钮/链接与 44px 操作高度已补齐；
- 当前 WebMCP 只凭首页 bridge/native registration 判断，公开 MCP server card 不等同 WebMCP；真实兼容浏览器任务保持 external gate。

验收证据：

- Node tests：9 pass；Python tests：42 pass；Node syntax check：pass；
- Python cross-runtime test 调用 Node builder，并用同一组 JSON Schemas 验证 readiness report、evidence ledger、quality report 和 manifest hash；
- 本地真实扫描 `https://beefapi.com`：Discoverable `pass`、Understandable `pass`、Actionable `partial`，`A-WEBMCP=fail`，AI visibility 与 business outcome 均 `not_measured`；
- 360px 真实渲染：页面宽度与 viewport 同为 360px，无整页横向溢出，Artifact Pack 与复制按钮均 44px 高，evidence table 在容器内滚动；
- Artifact Pack endpoint 回读为 HTTP 200，包含 input、ledger、quality report、canonical readiness report 和 manifest hashes；
- 本轮只进行公开路径只读扫描与本地 UI 验收，未运行兼容浏览器 WebMCP 任务，未 deploy、push 或写生产。

## Phase 8 — Packaging, Docs And Public Release Candidate

状态：`pass`

已完成：

- 补齐 CLI `run --text`、`eval` 和 `package --target source|unified|{capability-id}`；
- `source` 使用显式源码 allowlist 生成可复建 wheel 的 tarball；`unified` 生成包含 CLI、schemas、registry、root/child Skills、诊断 app 和公开文档的 wheel；
- 六个子 Skill 各自生成可直接解压到 Codex 或 Claude Code Skill 目录的 ZIP，包含入口、引用资产、MIT License、第三方声明和 SHA-256 package manifest；
- package gate 拒绝 path traversal、symlink、私有 home path、token-shaped secret、private key、Bearer token、缺许可证、缺引用资产和 wheel/source allowlist 逃逸；
- 完成 Codex 与 Claude Code 当前官方 Skill 目录说明、architecture、Artifact Protocol、contribution、security、release checklist、changelog 和两条 workflow 文档；
- 增加 BeefAPI 去隐私案例与完整 schema-valid Artifact Pack，删除客户、请求、财务、真实价格和内部运营信息；
- CI contract 已加入 repository validation、router eval、Python/Node checks 和全 package verification；
- release checklist 保留 human provenance review、commit、push、release 和公网部署为未执行 Owner gate。

最终本地发行候选：

| Target | Files | SHA-256 |
|---|---:|---|
| source tarball | 174 | `6fb41cbbd9a97e214656e615a969646fe749eaab132fd37db817c7b35fdb08f8` |
| unified wheel | 135 | `f026b2b4395f0a8582ed26fcdaae486017dd87400ced3ac24fb9ec1f3f3988d5` |
| geo-discover | 9 | `a6de8b41881dd57ba6ba3df8bda671e7a138e9d3f3aaf4e1b74de3f9b0d5ef1b` |
| geo-optimize | 15 | `7be636a611eb789ac4aa322ece2aaea6a818cf16256d122de3627e9855efab90` |
| geo-content | 9 | `bfc73b74fed328d16bee4780e4935666a909a28a9738d165c83ece6d785b70a5` |
| geo-measure | 10 | `da8b5b00422ae9b78c525e1a6e05bfc32d88c63d0d1c26ed27308fb202e6bf84` |
| seo-plan | 9 | `f8db9a87c53711621f19a1c4a8c96df05a74deba16dc58ef1171e0c81b2596fc` |
| webmcp-enable | 14 | `3689ceb7aef3b10c9d6906e15d007197495bb1f2487d3ba6c01401f932483393` |

验收证据：

- full repository validator：pass；Python tests：50 pass；Node tests：9 pass；Node syntax 和 `git diff --check`：pass；
- router eval：62/62，accuracy `1.0`，8 个 forbidden misroutes `0`，8 个 workflow precision `1.0`；
- source tarball 和 unified wheel 分别安装到两个全新虚拟环境，均完成 installed `list` 与 `validate`；
- unified wheel 在源码目录外完成 `read`、`eval`、`discover-diagnose` 和 `discover-content`，发布两个 schema/hash-valid 原子 run；
- 六个子 Skill 在六个临时安装目录解压后均可读取入口，所有相对引用均存在；
- package scan：0 private paths、0 receipts、0 user/customer data、0 token-shaped secrets、0 undeclared license、0 allowlist escape；
- 62-case router suite p95 `127.146 ms`；20 个确定性 workflow run p95 `27.115 ms`、max `28.435 ms`，低于 2 秒目标；
- 本地发行候选位于 `dist/release-candidate/`，目录被 gitignore，不构成公开发布。

## 2026-08-17 Productization Readback

### GitHub 与工作树

- GitHub 仓库仍为 public，默认分支 `main`；
- Draft PR [#1](https://github.com/Sunnyender-org/bflabs-agent-readiness/pull/1) 为 `OPEN`、`MERGEABLE`、`CLEAN`，head 为 `8bd65d428d4e67b3fdc1334ba32efce72695baaf`；
- PR 上两条 `validate / repository` check 均于 2026-08-11 `SUCCESS`；
- PR 未 merge，GitHub Releases 为空，未发现 package upload 或公网诊断部署证明；
- 本地 `README.md`、`AGENTS.md`、`docs/INDEX.md` 是先前未提交的文档治理改动，本轮保留；诊断 UI、测试与本进度文档的新变化同样尚未 commit/push。

### 四级 readiness 判断

| 层级 | 当前判断 | 证据与边界 |
|---|---|---|
| 本地可用 | `yes` | Node 14 tests、syntax check、Python 50 tests、62/62 router eval 均通过；本地服务可扫描真实公开站并下载 Artifact Pack |
| 可给人试用 | `controlled preview` | 技术用户可从当前分支本地运行，报告可交给 Agent，并可同站复测对比；尚无 merge/release/package upload，普通用户不是零安装自助 |
| 可公网开放 | `no` | 尚缺 DNS rebinding/pinning、防滥用、按客户端和目标限流、opt-out、保留/隐私策略及独立安全审查 |
| 商业闭环成立 | `partial` | 免费与付费边界、官方邮箱询盘、交付示例已连通；真实多平台采样、持续监测、跨系统实施回执和业务归因仍属于未交付的服务运营面 |

### 产品与数据闭环

```text
公开站诊断
  -> 三轴 readiness report + evidence ledger + Artifact Pack
  -> 免费开源 Skill + 绑定扫描指纹的 Agent 优化指令
  -> 客户/Agent 在本地仓库实施并验证
  -> 同站复测，生成三轴 Before / After
  -> 用户提供观测由 geo-measure 离线聚合
  -> BFLabs 付费层执行真实多平台重复抽样、趋势监测和跨系统交付
  -> 经客户授权连接 analytics / 转化 / 收入证据
  -> 分别报告 Readiness、AI visibility、Business outcome，不互相替代
```

### 本轮最小打磨

- “交给 Agent”现在一次下载 Artifact Pack 并复制包含目标、扫描指纹、三轴状态、失败项、unknown、最小子 Skill 路由、Owner gate 与复测要求的指令；
- 报告中的子 Skill 链接由当前 checkout 通过固定 allowlist 提供，不再错误依赖尚未 merge 的 GitHub `main` 路径；
- “保存基线并复测”把当前报告保存在页面内存，复测同站后展示真实三轴 Before / After；不上传或持久化基线；
- “联系 BFLabs”改为公开 `hello@bflabs.cn` 邮件入口，并预填目标、指纹、三轴结果和意向服务；
- Free 明确为公开诊断、开源 Skill 自助改站和本地复测；Paid 明确为跨系统实施、多平台抽样、持续监测和客户授权归因；
- 375px 视口无横向溢出，按钮和 tab 的最小操作高度统一为 44px。

### 当前真实扫描

2026-08-17 本地重新扫描 `https://beefapi.com`：Discoverable `100/pass`、Understandable `100/pass`、Actionable `100/pass`，六个固定公开路径均抓取成功，Artifact Pack HTTP 200 且 manifest/hash 文件齐全。与 2026-08-11 的 `100/100/75` 不同，是当前公开站证据变化，不应回写旧历史回执。

`A-WEBMCP` 当前只证明 bridge/native registration 可见，canonical report 仍标记 `present_unverified` 并保留 `compatible-browser-task-verification` external gate。没有运行真实兼容浏览器任务，AI visibility 和 business outcome 仍为 `not_measured`。

### 本轮验证回执

- `npm test --prefix app/readiness-web`：14/14 pass；
- `npm run check --prefix app/readiness-web`：pass；
- `uv run --isolated --with-editable . python scripts/skill_registry.py validate`：repository 与六个子 Skill pass，Python 50/50，router 62/62；
- `uv run --isolated --with-editable . python scripts/run_evals.py`：accuracy `1.0`，forbidden misroutes `0`，workflow precision `1.0`；
- `uv run --isolated --with pip --with-editable '.[dev]' python scripts/verify_packages.py`：source、unified、六个子 Skill 全部 pass，两个隔离 Python 安装、六个子 Skill 安装和两条 workflow run pass；
- source 与 unified 在系统临时目录完成构建和隔离验证；临时构建不构成 package upload，发布时必须从选定 commit 重建并生成最终 hash receipt；
- `git diff --check`：pass；
- 浏览器 1280px 与 375px 实测：375px `scrollWidth === innerWidth`，所有可见 `.button` 与 tab 均为 44px 高；基线复测、真实邮件 href 与 Before / After 页面均完成 readback。

## Remaining Goal

### P0

- 公网开放前完成 DNS rebinding/pinning、双维限流、防滥用、opt-out、保留/隐私策略和独立安全审查；
- Ender 分别决定本轮 commit/push、PR merge、GitHub Release/package upload 和公网部署；任一项都不能由本地验收替代。

### P1

- 把两次 Artifact Pack 的差异提升为可下载、schema/hash-valid 的 comparison artifact，而不只是在页面内展示；
- 为付费交付建立真实多平台重复采样、持续监测、跨系统实施和客户授权归因的可审计运行手册与 receipts；
- 完成 human provenance review，确认未复制 GEOHub AGPL 实现。

### P2

- 在获得真实试用反馈后，评估是否需要持久化项目历史、团队协作、报价/预约或 CRM 集成；当前不提前引入账号、数据库或 SaaS 依赖。

后续不得把本地 fixture、准备度分数、诊断结果或 package install 表述为真实外部 AI 可见度、业务结果、公网安全或已经发布。
