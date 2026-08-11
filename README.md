# BFLabs Agent Readiness

一个仓库完成网站面向 AI 的三段闭环：

```text
诊断网站 -> 优化网站 -> 验证结果
```

它把准备度拆成三个互不混淆的维度：

- **可发现 Discoverable**：公开页面和机器入口能否被找到。
- **可理解 Understandable**：产品、价格和接入事实是否清晰、当前且一致。
- **可操作 Actionable**：浏览器 Agent 是否能通过稳定入口或结构化工具完成任务。

准备度不等于 AI 排名、引用、推荐、订单或收入。真实平台可见度和业务结果需要独立测量。

## 仓库结构

```text
.
├── SKILL.md
├── app/
│   └── readiness-web/       # 本地只读诊断网站
├── skills/
│   ├── geo-optimize/        # GEO 与公开事实优化子 Skill
│   ├── geo-discover/        # 问题与机会发现子 Skill
│   ├── geo-content/         # 七种证据化内容生产模式
│   ├── geo-measure/         # 用户提供的 AI 回答观测聚合
│   ├── seo-plan/            # 证据化技术 SEO 规划
│   └── webmcp-enable/       # WebMCP 与 Agent Actionability 子 Skill
├── references/              # 产品边界与路由规则
├── evals/                   # 根 Skill 路由样例
├── examples/                # 去隐私案例与完整 Artifact Pack
├── workflows/               # 两条稳定工作流说明
└── scripts/                 # 仓库、eval 与发行包验证
```

## 能力注册表

当前注册表包含根入口和六个已运行子 Skill：

```bash
python3 -m pip install -e .
bflabs-readiness list --format markdown
bflabs-readiness route --text "先挖掘用户问题，然后诊断网站"
bflabs-readiness validate
```

统一 Artifact Protocol 支持单能力运行，也支持已验收的 `discover-diagnose` 原子工作流：

```bash
bflabs-readiness run \
  --capability geo-optimize \
  --input tests/fixtures/geo-optimize-audit-input.json \
  --output runs

bflabs-readiness run \
  --workflow discover-diagnose \
  --input tests/fixtures/discover-diagnose-input.json \
  --output runs

bflabs-readiness run \
  --workflow discover-content \
  --input tests/fixtures/discover-content-input.json \
  --output runs
```

成功运行会原子发布 `input/request.json`、`evidence-ledger.json`、`quality-report.json`、`run-manifest.json` 和 capability/workflow 输出。七项 v1 capability 均有真实入口、schema、质量门和测试，不暴露空实现。

中英文路由会选择一个最小 capability。只有用户明确要求“先发现再诊断”或“先发现再生产内容”时才返回 workflow DAG；两条稳定工作流都已通过纵向验收并以一个原子 run 执行。

## 当前六个子 Skill

### `geo-discover`

把受众、场景、比较、决策、价格/成本、接入和限制问题整理成可追溯的 query map 与 opportunity map。评分只使用覆盖缺口、证据缺口和明确业务相关性，不虚构搜索量。

[查看 Skill](skills/geo-discover/SKILL.md)

### `geo-content`

提供标题、科普解释、对比、带方法披露的榜单、页面蓝图、内容优化和 AI 友好改写七种模式。所有事实必须绑定证据；动态价格的 hash 或版本不一致会阻止产物发布。

[查看 Skill](skills/geo-content/SKILL.md)

### `geo-measure`

离线聚合用户提供的 ChatGPT、Gemini、腾讯元宝、豆包和 DeepSeek 回答观测，分别报告联网、站点引用、内容吸收、品牌出现、推荐与动态事实正确率。每项指标保留分子、分母、排除、缺失、Wilson 区间和平台/终端分层；普通网页搜索结果不会被计作模型回答。

[查看 Skill](skills/geo-measure/SKILL.md)

### `seo-plan`

为网站迁移、索引异常、国际化与技术 SEO 输出只读证据清单、优先检查、官方来源快照、实施前置条件和回滚要求。没有站点证据时只给 evidence gaps，不伪造失败 finding，也不会访问 Search Console、修改 CMS 或查询实时排名。

[查看 Skill](skills/seo-plan/SKILL.md)

### `geo-optimize`

在现有代码仓库中完成 evidence-backed GEO 审计、安全的本地修复和确定性验证。适合 `llms.txt`、答案页、动态定价、结构化数据与 Agent Actionability 审计。

[查看 Skill](skills/geo-optimize/SKILL.md)

### `webmcp-enable`

审计或实现 WebMCP，连接现有同源 MCP，并通过兼容浏览器验证代表性任务。真实 Cloudflare 配置、浏览器会话和写操作始终需要单独授权。

[查看 Skill](skills/webmcp-enable/SKILL.md)

## 本地诊断网站

```bash
cd app/readiness-web
npm test
npm run check
npm start
```

打开 `http://127.0.0.1:4177`，输入公开域名即可获得三轴报告、失败谓词、证据缺口、机会入口和最小子 Skill 路由。网页可下载统一 Artifact Pack，也可复制一段保留 unknown 和 Owner gate 的 Agent 优化指令。

网页保留旧 API response 作为兼容层，canonical `readiness_report`、evidence ledger、quality report 与 manifest 使用 CLI 相同的 JSON Schema 和 hash 规则。缺证据不会被换算成失败或分数；AI visibility 与 business outcome 始终独立显示为未测量。

当前网站是 promotion-candidate 原型，不应直接公开部署。正式公网扫描器仍需 DNS rebinding 防护、限流、滥用控制、保留策略与独立安全审查。

## 验证整个仓库

```bash
python3 -m pip install -e .
python3 scripts/skill_registry.py validate
python3 scripts/run_evals.py
npm test --prefix app/readiness-web
npm run check --prefix app/readiness-web
```

旧 `scripts/skill_registry.py list|read|validate` 入口保留为兼容 wrapper；新调用优先使用 `bflabs-readiness`。

## 发行候选包

```bash
bflabs-readiness eval
bflabs-readiness package --target source
bflabs-readiness package --target unified
bflabs-readiness package --target geo-optimize
python3 scripts/verify_packages.py
```

`source` 是显式 allowlist 的源码 tarball，`unified` 是可安装的 Python wheel，六个子 Skill 各自生成一个可直接放入 Agent Skills 目录的 ZIP。每个子包都包含 `SKILL.md`、被引用的 references/templates/examples/scripts、MIT License、第三方声明和带 SHA-256 的 package manifest。

隔离验证会在全新虚拟环境安装 unified wheel，回读七个 active capability，执行 62 条路由 eval，并真正跑完 `discover-diagnose` 与 `discover-content`。安装方法见 [Codex / Claude Code 安装说明](docs/install-codex-claude.md)，协议与架构见 [Artifact Protocol](docs/artifact-protocol.md) 和 [Architecture](docs/architecture.md)。

当前只形成本地 public release candidate。commit、push、GitHub Release、包上传和公网诊断站部署都需要 Ender 分别批准，见 [release checklist](docs/release-checklist.md)。

## BeefAPI 案例

BeefAPI 已具备公开模型发现、价格查询、分组比较、成本估算和接入指南等只读 MCP 工具。仓库中的[去隐私案例](examples/beefapi-readiness-case.md)和[完整 Artifact Pack](examples/beefapi-deidentified-artifact-pack.json)只表达可复现的准备度与任务证据，不包含客户、请求、财务或内部运营数据，也不承诺外部 AI 排名或收入归因。

## License

[MIT](LICENSE)

第三方启发、许可边界和 GEOHub clean-room 规则见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) 与 [licensing-and-attribution.md](references/licensing-and-attribution.md)。
