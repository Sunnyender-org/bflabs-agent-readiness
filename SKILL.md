---
name: bflabs-agent-readiness
slug: bflabs-agent-readiness
version: 0.6.1
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

## 先检查，再让你的 Agent 修

输入一个公开网站，看看 AI 能不能找到关键页面、读懂产品信息，并顺利完成下一步。诊断只读取公开内容，不登录，也不会直接修改网站。

[免费检查网站](https://readiness.bflabs.cn)

## 一个网站的完整一轮

只针对一个网站。先写清事实和目标。改任何页面之前，先看现在的 AI 怎么回答。再找出问题和对应页面，然后改。上线后，用同一批问题再问一遍，对比回答。最后看你自己的业务数据，写出这一轮的结果，并决定下一步。

想比较改完之后 AI 回答有没有变化，必须先留下改之前的记录。没有这份记录，就不能把之后的变化说成优化效果。

1. 写下必须正确的事实，以及你希望 AI 能答对的问题。
2. 改网站之前，先收集现在的 AI 回答。
3. 对照事实，找出答错的问题和对应页面。
4. 把提示词和网站仓库交给你自己的 Agent。
5. 你确认修改范围后，Agent 才开始改。由你决定何时部署。
6. 部署后再次检查。用同一批问题再问一遍，对比回答。
7. 如果你有业务数据，比较优化前后两段等长、不重叠时段的结果。没有业务数据，就先交付阶段报告，把业务结果标为未测。
8. 写清这一轮改了什么、回答有没有变化、下一步做什么。

中途停下也没关系。下次从还没做完的那一步继续。已经公开上线的改动，不要重做。

没有成交，不代表方法没用。但在真的有客人从看到走到付钱之前，也不能说这条路已经走通。

诊断站负责发现问题和说明下一步。真正的代码修改由你的 Agent 完成。

## 三种结果，分开看

- **网站是否准备好**：AI 能不能找到、读懂并使用网站。
- **真实 AI 平台表现**：网站有没有被引用或推荐，需要另外观察真实平台。
- **业务结果**：有没有带来线索、转化和收入，需要连接你授权的业务数据。

这三件事不会混成一个分数。网站准备好了，也不等于一定会被推荐或带来收入。

## 白帽做法

只写真实产品、真实经验和能核对的数据。页面给真人阅读、给真人继续办事，并用相关页之间的正常链接连起来。来源和日期按实际变更写。不要求把页面藏进导航，不编口碑，也不为了显得新而改日期。一份合法说明不在顶部菜单里，不算缺陷。

## 六种免费能力

- [发现客户真正会问的问题](https://readiness.bflabs.cn/skills/geo-discover)
- [把现有证据写成清楚的内容](https://readiness.bflabs.cn/skills/geo-content)
- [汇总你收集的 AI 平台回答](https://readiness.bflabs.cn/skills/geo-measure)
- [制定技术 SEO 改进计划](https://readiness.bflabs.cn/skills/seo-plan)
- [修复网站里的公开信息](https://readiness.bflabs.cn/skills/geo-optimize)
- [让 Agent 完成你允许的网站操作](https://readiness.bflabs.cn/skills/webmcp-enable)

每次只选择最适合当前问题的一种能力，避免把网站一次改乱。要做完整一轮，用下面的启动提示词。

## 免费自助与 BFLabs 服务

整套方法都免费。包括完整一轮怎么做、检查规则、模板和报告格式。

你自己准备 Agent、网站权限、平台账号或手头的回答记录，以及你自己的业务数据。

BFLabs 的服务，是由 BFLabs 来做这些事：改站实施、反复抽样、托管记录、持续盯着变化，以及后续复查。

联系 BFLabs：hello@bflabs.cn

## 固定启动提示词

复制下面这段话，发给你正在用的 Agent，把最后一行换成你要做的事。

```
请先阅读 https://readiness.bflabs.cn/skills/bflabs-agent-readiness。配套说明在同一地址下 manifest.json 列出的文件里。读完后，只向我要完成当前这件事还缺的信息。不要让我挑选要使用哪一项能力，不要让我填技术表单，也不要让我配置 MCP。
我要做的事：（写下网站地址和你想解决的问题。如果已经做过一部分，写上项目文件夹的位置。）
```

## 公开榜单

榜单默认不会公开你的网站。只有你主动选择时才会上榜；已经加入后，也可以联系 BFLabs 申请移除。

<!-- AGENT_ONLY: For a locally loaded package, first read references/root-agent-contract.md relative to that package and use its local companions. For an online entry, read https://readiness.bflabs.cn/skills/bflabs-agent-readiness/references/root-agent-contract.md and follow it. Manifest: https://readiness.bflabs.cn/skills/bflabs-agent-readiness/manifest.json. Never project its implementation language into rendered product copy. -->
