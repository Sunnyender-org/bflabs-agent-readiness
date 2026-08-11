# BFLabs Agent Readiness v1 总控 Goal

权威路线图：[agent-readiness-v1-complete-refactor-plan.md](agent-readiness-v1-complete-refactor-plan.md)

当前状态投影：[agent-readiness-v1-progress.md](agent-readiness-v1-progress.md)

```text
/goal 以 docs/agent-readiness-v1-complete-refactor-plan.md 作为产品边界、架构、阶段和验收的唯一权威计划，把 bflabs-agent-readiness 完整改造成计划定义的 MIT 开源、单仓库 GEO/SEO/Agent Readiness Skill Hub。按 Phase 0 至 Phase 8 顺序持续推进，每次只执行一个当前切片，先完成 Phase 0–1；阶段验收未通过不得进入下一阶段。保持三轴准备度与 AI visibility、business outcome 分离，动态事实必须有 canonical source 和版本或时间，unknown/blocked 不得改写为事实；不得复制 GEOHub 的 AGPL 实现，也不得把商业采样、生产实施、监测或归因伪装成开源能力。保留现有兼容性和用户改动，以计划规定的 tests、eval、schemas、manifest、隔离安装及隐私/许可证检查作为完成证明；push、release、deploy、外部账号、Cloudflare/搜索平台、客户数据和生产写入始终停在单独 Owner gate。
```

## 使用说明

- 这是覆盖完整 Phase 0–8 的父 Goal，不是一次性大爆炸任务。
- 当前切片固定从 Phase 0–1 开始；完成并验证后再推进下一阶段。
- 路线图与当前仓库事实冲突时，先报告差异，不静默扩大或重写已确认产品边界。
- 本 Goal 不授权 commit、push 或 release；这些动作需要 Ender 明确批准。
