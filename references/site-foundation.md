# Site foundation

Agent-only assembly contract for M2. User-visible sentences are Chinese. Actual page files and deploy commands belong to the host Agent or an existing site tool. This repository does not add a general site builder.

Read `references/whitehat-method.md` for M2-site-foundation, M2-information-architecture, and M2-action-entry. Use the existing seo-plan and geo-content Skills; do not invent a third builder Skill.

## What site foundation covers

网站基础包括：定位、信息架构、首页、产品或价格、文档、政策、正常内链、域名与 HTTPS、可读性、移动端、性能、基础发现设置，以及能完成下一步的业务入口。

复杂产品重构、支付渠道、客户系统和全栈技术课按独立项目处理，不自动并入这一轮。

## Prefer the current site

已有网站先补缺口，不重建。

1. 盘点现成的首页、产品或价格页、文档和政策页。
2. 看这些页能不能回答本轮问题、承接下一步。
3. 能共用就共用。多个问题可以落在同一页。
4. 只有内容实质不同、且能独立帮人完成任务时，才新增一页。
5. 六个问题不强制六张新页。首轮常见是先看三张代表页；这是项目假设，不是已证明的结构。

一份合法说明不在顶部菜单里，只要人能从页脚或相关页到达，就不算缺陷。不要为了测量来源而把页面从人类导航和相关内链里藏起来。

## No site yet

还没有网站时，交付最小可实施网站和部署交接，不虚构公开地址。

最小可发布范围通常是：

- 一句话定位：服务谁、解决什么、下一步做什么。
- 首页：对象、能力和限制。
- 产品或服务页：关键事实和下一步。
- 必要政策页：例如隐私或退款，可从页脚到达。
- 域名、HTTPS，以及能打开的行动入口。
- 相关页之间的正常链接。
- 基础发现：可抓取、有规范地址；sitemap 帮助发现，不保证收录。

“只帮我建网站”是建设任务，不强迫先做整轮 AI 采样。从零建站并做一轮 GEO 时，首次上线本身就是干预：有条件可先记录还没有公开地址时的品牌或类别回答；解释类问题标不适用或未测，不造零分。

设计稿、本地实现和功能测试可以先行。公开发布需要当前项目的明确授权。首次上线后，再建立可读站点基线，供以后比较。若比较建站前后，结论必须写明改变的是整个网站可用性，不能说只是某一项技巧造成。没有任何改前样本时，交付上线状态和后续观察，不补造基线。

`https://global.beefapi.com/` 是已有站点，不能替无站点路径完成真实验收。本文不填写该站的采样或收入结果。

## Handoff

免费方法给出流程和验收。宿主 Agent 负责实际搭页面、改仓库和部署。交接时写清：

- 要发布哪些页，每页解决什么问题。
- 哪些事实必须和来源一致。
- 谁来部署、部署到哪里、怎样读回公开地址。
- 哪些项未做，为什么未做。

没有公开地址时，不要生成整轮实验记录，也不要假装已经有可复测的线上基线。

## How existing Skills help

- seo-plan: 在没有站点、只要建设、或现站缺发现与技术基础时，列出只读检查、证据缺口和需主人批准的实施项。不保证收录、排名或增长。
- geo-content: 按证据写首页、产品、文档或政策页的正文结构。优先改已有页。多问共用一页时，不要把观察线或意图标签合并。
- geo-optimize: 在已有仓库里核验公开事实、三层可读性和行动入口。

A technically correct plan is not a rebuilt website and not a growth result.
