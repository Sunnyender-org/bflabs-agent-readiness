# BFLabs Agent Readiness v1 Progress

更新时间：2026-08-23

```text
进度罗盘：BFLabs Agent Readiness v1 complete refactor
位置：0.4.1 已上线 / 0.4.2 SkillHub 包卫生补丁本地进行中
状态：PR #5 merged、v0.4.1 released、readiness.bflabs.cn 0.4.1 live、skills.bflabs.cn GEO catalog live；外部 SkillHub 尚未接受
本轮：生产验证两个站点；补齐官方 SkillHub 元数据和 BFLabs Logo；撤下误含本地 Wrangler cache 的 0.4.1 source asset
下一关口：提交/合并/发布 0.4.2，使用平台专用 ZIP 提交 SkillHub 并读取审核状态；独立安全复核仍单列
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

本文件记录当前 live readback，但不是独立安全 Verifier 签字。发布与部署证明分别来自 GitHub Release、Cloudflare production readback 和真实邮件收件；它们不证明 AI visibility 或 business outcome。

## 2026-08-18 Local Paid-Delivery Prototype

- 公网诊断的 Agent handoff 现只选择第一个 evidence-backed owner Skill，不再默认同时推荐发现、测量、SEO 与内容 Skill；报告仍只陈述当前公开网站状态；
- 建立独立本地目录 `bflabs-geo-delivery`，内部含可移植 engagement JSON、authority scopes、三层状态、确定性校验脚本、合成 fixture 和 WorkBuddy `/geo-delivery` 薄入口；
- WorkBuddy 被限定为 cockpit，不保存唯一真相；engagement 文件可被 WorkBuddy、Codex 或人工流程共同使用；
- 私有合同明确分离 readiness、AI visibility、business outcome，缺证据保持 `not_measured`，并拒绝 secret-shaped 字段、无证据的 measured 状态，以及未授权的平台/业务 evidence；
- 本地验证：公开仓库 Python 50 tests、router 62/62、诊断 Web 19 tests、syntax/Worker build pass；私有交付合同 7 tests、合成 engagement validate/status、plugin manifest JSON 和 Skill 官方 quick validator 均 pass；Python 总门禁通过 `uv` 隔离依赖环境运行，不改变系统 Python；
- 上述改动均为本地未提交状态；WorkBuddy 未安装此插件，未创建远端仓库，未进行真实客户采样、账号登录、生产写入、发布或部署，因此商业闭环判断仍为 `partial`。

## 2026-08-22 Prompt-first And Agent-native Productization

- 结果页把“复制给 Agent，开始修复”提升为三轴后的第一主动作；复制不再强制下载 Artifact Pack，提示词包含扫描指纹、站点托管根 Skill、唯一子 Skill、当前证据、测试要求和部署边界；
- 根 Skill 与六个子 Skill 通过 `/skills/{id}` 和 `/.well-known/agent-skills/index.json` 提供，索引绑定 SHA-256；本地 BF Labs Skills 目录已把 GEO 标为 SkillHub host，并改用稳定站点 URL；
- 新增确定性 Agent Journey：基于本次公开响应执行“进入、理解、找到下一步”三步试跑，并最多继续读取一个选中的同源公开入口；不执行页面指令、不提交表单、不登录、不增加外部模型成本；合同固定 `affects_readiness_score=false`，AI visibility 与 business outcome 保持 `not_measured`；
- 新增 opt-in 公开榜单：默认不公开，只有请求显式选择时才写入；记录仅含 canonical origin、三轴、指纹和时间，不含证据正文、Prompt 或 IP，KV 最多保留 30 天；排序依次使用通过轴数、最弱轴和三轴平均分，不生成隐藏总分；每个已上榜域名有服务端可读的独立分享页，避免榜单只靠客户端 JSON 而失去搜索流量价值；
- 新增 `/api/v1/scans`、`/api/v1/leaderboard`、版本化 ruleset、`text/markdown`、OpenAPI、`llms.txt`、RFC-style `code/detail/resolution` problem responses、`bflabs-readiness scan` CLI 和四个 MCP tools；网页、CLI、Markdown 和 MCP scan 返回同一报告合同；
- executable scenarios 4/4：默认私有、明确公开、存储未配置降级、Journey 不越过测量边界；生产 truth owner 为 `app/readiness-web/src/leaderboard.mjs` 与 `app/readiness-web/src/scanner.mjs#buildAgentJourney`，没有第二套评分或 Journey evaluator；
- 本地验证：Node/Worker 31 tests、Python 53 tests、router 62/62、repository validator、Skill quick validator、Worker build、OpenAPI JSON、SkillHub JS syntax 全部 pass；0.4.0 source 207 files、unified wheel 156 files、六个 child packages、两个隔离安装和两个 workflow runs全部通过 package verification；CLI→公网扫描→Markdown→显式上榜→榜单读回与 MCP/Skill index 实际链路通过；桌面与 390px 页面均完成浏览器检查且无横向溢出；
- 2026-08-22 本地新扫描器对当前 `https://beefapi.com` 的公开读回为 Discoverable `100`、Understandable `100`、Actionable `100`，确定性 Journey `pass`，发现 6 个公开 MCP tools；由于兼容浏览器真实任务仍未执行，WebMCP 继续是 `present_unverified`，该结果不升级 AI visibility 或 business outcome；
- PR [#4](https://github.com/Sunnyender-org/bflabs-agent-readiness/pull/4) 已 merge 为 `8cebb0801f9cb809d50716d61fc424945e74522e`，两项 GitHub Actions 均通过；GitHub Release [`v0.4.0`](https://github.com/Sunnyender-org/bflabs-agent-readiness/releases/tag/v0.4.0) 已从该 merge commit 发布八个带 SHA-256 digest 的资产；
- Cloudflare Worker 版本 `f626760b-73c3-4332-9b9e-1a48381ed44e` 已绑定 `LEADERBOARD` KV、客户端/目标限流和 Assets；生产读回验证首页、榜单、隐私、条款、OpenAPI、`llms.txt`、Agent Skills、MCP card、methodology 与根 Skill 均为 200；
- 生产默认私有扫描后榜单仍为空；显式 opt-in 的 `beefapi.com` 写入成功，KV 控制面读到 `entry:beefapi.com` 与到期时间，公开 API 和独立分享页均可读；生产 Markdown、MCP `tools/list` 和 0.4.0 wheel CLI 扫描均通过；
- 生产 BeefAPI 扫描为 Discoverable `100`、Understandable `100`、Actionable `75/partial`，确定性 Journey `pass`；AI visibility 与 business outcome 均保持 `not_measured`。外部 SkillHub、Lucas 邮箱验证与真实付费交付仍未因此成立。
- PR #5 已 merge 为 `e32788a0e0a5a672d0c898589f6d3387700bcd4a`，Release `v0.4.1` 与 Worker `e9ab84ad-34df-4301-b8d7-5439c3b41235` 已发布；线上根 Skill 读回官方 SkillHub 元数据与 BFLabs Logo 引用；
- `bflabs-skills` PR #3 已 merge 为 `b46ec827d47b0da880053b98230b155b87442ed1`，Worker `ea9d6bb1-9724-43a0-bb4b-163cf2d6b12e` 已部署；目录、宿主、层级和安装页生产 200；
- SkillHub 首次真实提交因 218 个文件超过平台 200 上限而未创建 listing；第二次缩包被平台拒绝无扩展名 `LICENSE`。随后审计发现 0.4.1 source tarball 带入本地 `.wrangler` 和 `.worker-build`；该 source asset 下载数为 0，已从 GitHub Release 撤下，wheel 和六个 child Skill 资产不受影响。0.4.2 将在构建器层永久排除这些目录，并生成平台允许的专用 ZIP。

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

## 2026-08-17 Productization And Launch Readback

### GitHub、Release 与生产

- PR [#1](https://github.com/Sunnyender-org/bflabs-agent-readiness/pull/1) 已于 2026-08-16 17:18:51 UTC merge，merge commit 为 `7aa7b9e1e366b795c4d0e0d523f60bdc24c85185`；
- GitHub Release [`v0.3.0`](https://github.com/Sunnyender-org/bflabs-agent-readiness/releases/tag/v0.3.0) 已发布，包含 source tarball、unified wheel 与六个 child Skill ZIP，共八个带 GitHub SHA-256 digest 的资产；
- 邮件 fanout follow-up commit `dd87282c4b453bbf76904d68c0e4ee870bf5f6f9` 已 push 到 `main`，对应 GitHub Actions run `31961670907` 全绿；
- Cloudflare Worker `bflabs-agent-readiness` 已部署到 [readiness.bflabs.cn](https://readiness.bflabs.cn)，不覆盖现有 `bflabs.cn` 官网；
- 生产首页、隐私页、ruleset API 均 HTTPS 200；生产拒绝 loopback literal target 为 400；真实生产扫描 `https://beefapi.com` 为 Discoverable `100`、Understandable `100`、Actionable `75/partial`，Artifact Pack `pass`；
- Cloudflare Email Routing 为 `enabled / ready`，`hello@bflabs.cn` 进入同一 Worker。主收件箱已验证并由 Ender 确认收到真实 smoke 邮件；Lucas 目标仍为 `pending`，不得称双邮箱已完成。

### 四级 readiness 判断

| 层级 | 当前判断 | 证据与边界 |
|---|---|---|
| 本地可用 | `yes` | Python 50 tests、Node/Worker 18 tests、62/62 router eval、完整 package verification 均通过 |
| 可给人试用 | `yes, public beta` | 零安装公网诊断、Artifact Pack、Agent handoff、同站 Before/After 与公开 Skill release 均可用 |
| 可公网开放 | `public beta live` | strictly-public fetch、双维限流、大小/超时/重定向上限、opt-out、无应用数据库留存与 observability 已上线；独立安全审查仍未签字，因此不是无保留的 production security sign-off |
| 商业闭环成立 | `partial` | 免费入口、开源 Skill、复测与真实邮件询盘已连通；真实多平台采样、持续监测、跨系统实施 receipts 和客户授权业务归因仍是付费运营缺口 |

### 产品与数据闭环

```text
公网诊断
  -> 三轴 readiness report + 独立 Agent Journey + evidence ledger
  -> 可选公开三轴摘要到榜单（默认关闭）
  -> Prompt-first：站点托管根 Skill + 唯一子 Skill + 扫描指纹
  -> Artifact Pack 作为高级证据下载
  -> 客户/Agent 在本地仓库实施并验证
  -> 同站复测，生成三轴 Before / After
  -> geo-measure 聚合真实平台观测，单独报告 AI visibility
  -> hello@bflabs.cn 进入 BFLabs 付费咨询与跨系统交付
  -> 持续复测、多平台重复采样与实施 receipts
  -> 经客户授权连接 analytics / 转化 / 收入证据
  -> 分别报告 Readiness、AI visibility、Business outcome，不互相替代
```

### 生产安全与隐私边界

- Worker 启用 Cloudflare `global_fetch_strictly_public`，拒绝 IP literal、private-style hostname、不安全端口与重定向；
- Cloudflare Rate Limiting bindings 分别按客户端哈希和目标 hostname 限制，扫描请求与目标响应都有大小、重定向和逐请求超时上限；
- 报告和 baseline 留在浏览器，不写应用数据库；Cloudflare 基础设施日志仍受其平台策略约束；
- 站点可通过 `/.well-known/bflabs-agent-readiness-opt-out` 明确拒绝诊断，滥用报告进入 `hello@bflabs.cn`；
- `A-WEBMCP` 仍为 `present_unverified` 并保留真实兼容浏览器任务 external gate；AI visibility 与 business outcome 均保持 `not_measured`。

## Remaining Goal

### P0

- 将已创建的 `LEADERBOARD` KV binding 随 Worker 部署，并生产复核默认不上榜、summary-only、30 天保留、目标 opt-out 与移除/滥用响应路径；
- 部署并读回本轮 Prompt-first/API/CLI/MCP/Journey/Skill index；独立安全审查仍需单独签字；
- 完成外部 SkillHub 平台提交并读取 accepted listing receipt；当前只有 `skill.yml` 与本地目录准备完成；
- Lucas 在其 QQ 邮箱完成 Cloudflare destination verification；完成前主邮箱可用，但双邮箱 fanout 不算完成；
- 完成独立安全审查并记录签字；当前只能称 public beta live，不能称完整安全签署。

### P1

- 把两次 Artifact Pack 的差异提升为可下载、schema/hash-valid comparison artifact；
- 为付费交付建立真实多平台重复采样、持续监测、跨系统实施和客户授权归因的可审计运行手册与 receipts；
- 完成 human provenance review，确认未复制 GEOHub AGPL 实现。

### P2

- 根据真实试用反馈决定是否引入项目历史、团队协作、报价/预约或 CRM；当前不把这些未交付能力写入商业完成声明。

后续不得把 readiness 分数、诊断结果或 package install 表述为真实外部 AI 可见度或业务结果；也不得在 Lucas destination 仍 pending 时声称邮件双投递完成。
