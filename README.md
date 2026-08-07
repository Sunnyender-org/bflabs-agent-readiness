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
│   └── webmcp-enable/       # WebMCP 与 Agent Actionability 子 Skill
├── references/              # 产品边界与路由规则
├── evals/                   # 根 Skill 路由样例
└── scripts/                 # 仓库检查与受限 SOP registry
```

## 两个子 Skill

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

打开 `http://127.0.0.1:4177`，输入公开域名即可获得三轴报告。

当前网站是 promotion-candidate 原型，不应直接公开部署。正式公网扫描器仍需 DNS rebinding 防护、限流、滥用控制、保留策略与独立安全审查。

## 验证整个仓库

```bash
python3 scripts/skill_registry.py validate
npm test --prefix app/readiness-web
npm run check --prefix app/readiness-web
```

## BeefAPI 案例

BeefAPI 已具备公开模型发现、价格查询、分组比较、成本估算和接入指南等只读 MCP 工具。仓库中的公开示例只表达可复现的准备度与任务证据，不承诺外部 AI 排名或收入归因。

## License

[MIT](LICENSE)
