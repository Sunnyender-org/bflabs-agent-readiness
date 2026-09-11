# 白帽 GEO 方法

Agent-only method source. Teaching, Skills, and reports use the same words. User-visible sentences are Chinese. Method IDs and maturity values stay exact.

This file is the public method. Product prices, models, and customer facts live only in each project's fact record. Do not keep editable copies here.

First practice site: `https://global.beefapi.com/`. This file does not contain sampled answers, traffic, or revenue for that site.

## Shared vocabulary

Keep these five ideas separate. They can describe the same person and the same order. They must not be added together, and they must not be renamed as increment.

| Term | 中文 | Meaning | Business example | Must not infer |
| --- | --- | --- | --- | --- |
| discovery channel | 发现渠道 | How the person first learned the product exists | 用户自报：最早在一篇教程里知道这个接口服务 | 不能把这次浏览器来源改写成第一次发现 |
| arrival channel | 到站渠道 | How this visit reached the site | 这次访问的来源是 Google | `google.com` 是搜索到站，不是 AI |
| page touch | 页面接触 | Which public page was opened | 打开了接入说明页 | 打开某页不能证明来自某次 AI 回答 |
| paid | 实付 | Money that actually cleared, after status and refunds | 一笔已支付订单 | 待付、失败、测试、充值余额不是确认收入 |
| increment | 增量 | Extra outcome caused by a defined change | 尚未具备对照时，只写观察，不写增量 | 有来源的实付不是优化带来的新增收入 |

Also keep four result layers separate:

- 网站准备度：人能不能找到信息并做下一步，AI 能不能读到同一批事实。
- 真实 AI 表现：真实平台有没有提到、引用或推荐。
- 已观察业务结果：授权记录里实际发生的到访、注册、调用和实付。
- 优化增量：只有合适对照时才能谈；完成一轮工作本身是可交付结果。

没有客人从看到走到付钱，不能说获客已经走通。没有成交，也不等于方法没用。

## Positive whitehat

只写真实产品、真实经验和能核对的数据。页面给真人阅读、给真人继续办事，并用相关页之间的正常链接连起来。来源和日期按实际变更写。

不要求把页面藏进导航。不编口碑、评价或权威。不为了显得新而改日期。一份合法说明不在顶部菜单里，只要人能从页脚或相关页到达，就不算缺陷。

公开地址仍可能从搜索、转发或书签进来。缺来源时保持未知，不要补成 AI。

## Maturity

Use exactly one of: `platform_docs` | `general_method` | `project_hypothesis` | `case_observation` | `multi_case_review` | `revised`.

Do not raise maturity because one case looked good. A later practice may refute a step; record that in `references/method-evidence.md` and `templates/method-review.md`.

---

## M1 目标与白帽原则

### M1-purpose

- **question**: 服务谁、解决什么真实问题、期望用户完成哪一步？
- **principle**: 每个项目先写清服务对象、真实任务和下一步有效行为。指标必须能取到证据；取不到就标未测。
- **applicable_when**: 开始任何一轮之前。首个实践站是面向英文开发者的 `https://global.beefapi.com/`；该站把首次成功 API 调用当作核心业务行为，是项目假设，不是已测结果。
- **actions**: 写下对象、任务、权威事实来源、阶段指标，以及每一项对应的证据或未测。把充值额、消费额、净收款和利润分开。
- **counterexample**: 把“让 AI 必须推荐我们”写成目标，或把尚未发生的收入当成这轮已经完成的结果。
- **acceptance_evidence**: 每项目标都能指向可取得的证据，或明确写未测；没有把未测项写成已成功。
- **sources**: [Google 生成式搜索优化指南](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide)
- **maturity**: `general_method`

### M1-whitehat

- **question**: 怎样写内容和做页面，才是在帮人和 AI 核验真实信息，而不是在制造信号？
- **principle**: 白帽建立在真实产品、经验和可核对数据上。人和 AI 看到同一批事实。独立、相关、可信的第三方引用有价值；购买排名链接不是本方法。
- **applicable_when**: 规划页面、写正文、加来源或日期时。
- **actions**: 先整理企业事实，再写对真人有用的内容。保留真实来源和实际变更日期。用正常内链连接相关页。
- **counterexample**: 伪造测评或口碑；给机器单独藏一套和真人不同的断言；要求答案页离开所有人类导航，再把无来源访问当成 AI。
- **acceptance_evidence**: 正文可被真人读完并继续办事；来源和日期能对上实际变更；没有把合法政策页不进顶部菜单判成缺陷。
- **sources**: [姚金刚 2026-09-10 白帽与黑帽](https://x.com/yaojingang/status/2097981782092349821)；[Google 垃圾内容政策](https://developers.google.com/search/docs/essentials/spam-policies)
- **maturity**: `platform_docs`

### M1-stage-metrics

- **question**: 这一轮结束时，准备度、AI 表现、业务结果和增量各证明了什么？
- **principle**: 四层证据分开看。完成一轮是交付结果。关联收入可以按限定口径报告；不能改称增量。
- **applicable_when**: 写阶段报告、对外说明或比较前后时。
- **actions**: 分别报告网站是否可访问可读、真实平台观察、授权业务记录，以及对照是否足够谈增量。缺数据就交阶段报告，并标未测。
- **counterexample**: 把准备度分数、提及次数和实付加总成一个获客分；或把 Google AI 展示量当成订单来源。
- **acceptance_evidence**: 报告里四层各有分母或未测说明；视图金额未相加。
- **sources**: [Google 生成式 AI 展示报告](https://developers.google.com/search/blog/2026/06/gen-ai-performance-reports)；[Profound 与 Analytics 关联](https://www.tryprofound.com/blog/google-analytics)
- **maturity**: `general_method`

---

## M2 网站基础与承接

### M2-site-foundation

- **question**: 现在有没有一个能公开访问、能读完、能做下一步的网站？
- **principle**: 需要时先补网站基础。已有站优先修现页，不重建。没有网站时，只做最小可实施网站和部署交接。实际搭建归宿主 Agent 或既有建站工具。
- **applicable_when**: 没有公开站点、只有建设任务、或现站缺首页/产品/文档/政策/行动入口时。只建站时，不强迫先做整轮 AI 采样。
- **actions**: 按 `references/site-foundation.md` 盘点定位、信息架构、必要页面、域名与 HTTPS、可读性、移动端、性能、基础发现和行动入口。没有站点就交出最小页面清单和部署交接，不虚构公开地址。
- **counterexample**: 因为第一个案例站已经存在，就把无站点路径留空；或在本方法里新增通用建站引擎。
- **acceptance_evidence**: 无站点案例有可实施的最小网站和部署交接；已有站点没有被写成推倒重来。
- **sources**: [Google 生成式搜索优化指南](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide)
- **maturity**: `general_method`

### M2-information-architecture

- **question**: 用户和抓取工具能不能从相关页找到需要的信息？
- **principle**: 题目和页面允许多对多。相同任务优先维护一个权威页。不需要为每个问法单独建页。重要内容应能从相关内链到达；不必全部进入顶部导航。
- **applicable_when**: 映射问题与页面、新增或合并页面时。
- **actions**: 先看首页、产品/价格页、接入文档和已有说明能否承担问题。只有内容实质不同、且能独立帮用户完成任务时才新增页面。六个问题不强制六张新页。
- **counterexample**: 预设六道题就要六张新答案页；或把不进主导航本身当成来源证明。
- **acceptance_evidence**: 每个冻结问题都有页面归属；共用页没有被拆成空壳变体页。
- **sources**: [Google 生成式搜索优化指南](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide)；[Microsoft 内容指导](https://about.ads.microsoft.com/en/blog/post/october-2025/optimizing-your-content-for-inclusion-in-ai-search-answers)
- **maturity**: `platform_docs`

### M2-action-entry

- **question**: 读完信息后，用户能不能完成下一步？
- **principle**: 每个代表页都应指向一个真实、当前可用的下一步：阅读文档、注册、调用或购买。入口必须和正文事实一致。
- **applicable_when**: 首页、产品页、文档页或政策页已经能说明事实，但下一步不清楚或不可用时。
- **actions**: 在正文里写清下一步、所需条件和失败时怎么办。核验链接、表单或调用入口在公开地址上可用。复杂支付、CRM 或全栈重构不自动并入本方法。
- **counterexample**: 只堆介绍文字，没有可完成的下一步；或把不能使用的按钮写成已开通。
- **acceptance_evidence**: 代表页有可核验的行动入口；不可用入口被记为缺口，而不是已完成。
- **sources**: [Google 生成式搜索优化指南](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide)
- **maturity**: `general_method`

---

## M3 事实与真实问题

### M3-fact-cards

- **question**: 哪些事实可信，依据是什么，何时生效、何时核验、正文何时实质更新？
- **principle**: 关键断言连到公开来源。已核验、用户提供、待核验和证据不足要分开。生效、核验和正文实质更新是三种时间。
- **applicable_when**: 整理价格、模型、限制、退款、兼容性或任何会变化的事实时。
- **actions**: 为每条事实写下陈述、来源、生效时间、核验时间和正文是否因此改过。人和机器视图使用同一批事实。禁止项和冲突项不进入对外正文。
- **counterexample**: 只重新核验就把内容更新日改成今天；或问现价时用旧价，却因为页面写过日期而算答对。
- **acceptance_evidence**: 每条采用事实都有来源和时间类型；重新核验没有被写成正文已更新。
- **sources**: [Yao 事实规则](https://github.com/yaojingang/yao-geo-skills/blob/201c0c45dcf09bb37bc46a467b4baf4d721db205/skills/yao-geo-content-refiner/references/evidence-and-fact-rules.md)；[Google 发布日期](https://developers.google.com/search/docs/appearance/publication-dates)
- **maturity**: `general_method`

### M3-question-sources

- **question**: 用户究竟怎么问，这些问句从哪来？
- **principle**: 用户自报、客服记录、站内搜索、平台导出和 Agent 假设必须分开。假设不能冒充真实搜索量。
- **applicable_when**: 收集或冻结本轮问题，或把新问题放入下一轮候选池时。
- **actions**: 记录每道题的出处、采集时间和市场。只在用户自报先通过 AI 知道产品后，才追问当时的原话。允许跳过或不记得。
- **counterexample**: 用合成监测题冒充真实用户问题，或把假设题写成已验证搜索量。
- **acceptance_evidence**: 每道题能看出来源类型；假设题没有进入真实搜索量口径。
- **sources**: [PostHog 真实问题实践](https://newsletter.posthog.com/p/llms-are-picking-winners-heres-how)
- **maturity**: `general_method`

### M3-question-page-map

- **question**: 这道题现在由哪一页回答，要不要新开一页？
- **principle**: 先映射到已有权威页。多问可以共用一页。只有独立任务和实质不同的内容才拆页。
- **applicable_when**: 已有冻结问题，正在选择代表页或改动范围时。首轮常见做法是先看首页、一张价格或产品页、一张接入文档；这是项目假设，不是已证明的最佳页数。
- **actions**: 为每道题写下页面用途和选择理由。共用页列出全部承担的问题。不要为了制造对照而预建空答案页。
- **counterexample**: 六问强制六张新页；或先上线整批答案页再去采改前基线。
- **acceptance_evidence**: 问题与页面映射完整；新增页都有独立用途，而不是问法变体。
- **sources**: [Google 生成式搜索优化指南](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide)
- **maturity**: `platform_docs`

---

## M4 基线与测量设计

### M4-frozen-set

- **question**: 改之前用哪一组题比较，改之后还能不能用同一组题？
- **principle**: 本轮题库在改站前冻结。新问题进入下一轮候选池，不改本轮分母。改题、改依赖事实或改评分规则，都要新版本和新基线。
- **applicable_when**: 准备采样、改内容或复测之前。
- **actions**: 写下题面、事实版本、评分规则和冻结时间。看到结果后不得放宽题目。旧题和旧结果不被覆盖。
- **counterexample**: 发现答不好就改题再测，却仍声称和改前同一组题可比较。
- **acceptance_evidence**: 改前记录早于公开改动；新问题没有换掉本轮分母。
- **sources**: [Yao 效果指标](https://github.com/yaojingang/yao-geo-skills/blob/201c0c45dcf09bb37bc46a467b4baf4d721db205/skills/yao-geo-effect-monitor/references/metrics-attribution.md)
- **maturity**: `general_method`

### M4-environment

- **question**: 这次观察是在哪个平台、哪种入口、什么地区和语言下得到的？
- **principle**: ChatGPT、Perplexity 和 Google Search 是不同观察面。同一产品的 API、App 和网页也要分开。入口不同，不能配成一对。
- **applicable_when**: 采集或导入任何 AI 或搜索观察时。
- **actions**: 记录平台、入口、可见模型、语言、地区和个性化设置。Google Search 的普通网页结果不是模型回答。Gemini 聊天若采集，单列，不替代 Google Search。
- **counterexample**: 把 API 回答当作网页实测；或把一次 google.com 来访写成 AI Overview 点击。
- **acceptance_evidence**: 每条观察都能还原平台和入口；不可比的入口没有被配对。
- **sources**: [Google AI 功能说明](https://developers.google.com/search/docs/appearance/ai-features)
- **maturity**: `general_method`

### M4-observation-window

- **question**: 改前是什么状态，之后用哪一段窗口比较？
- **principle**: AI 采样窗和业务观察窗相互独立。三次重复只用于流程试跑和方向观察，不是显著标准。不拿成熟 cohort 和未成熟 cohort 当同等比较。
- **applicable_when**: 设计基线、复测日或业务前后比较时。
- **actions**: 分别写下 AI 采样时间和业务前后窗口。窗口边界不双计。比较时写明截至时间。没有改前样本就不补造基线。
- **counterexample**: 公开改完内容再去补“改前”回答；或用 30 天老用户对比只观察 3 天的新用户。
- **acceptance_evidence**: 改前记录可核对且早于公开改动；业务窗和 AI 窗能分开成立。
- **sources**: [Yao 效果指标](https://github.com/yaojingang/yao-geo-skills/blob/201c0c45dcf09bb37bc46a467b4baf4d721db205/skills/yao-geo-effect-monitor/references/metrics-attribution.md)
- **maturity**: `general_method`

---

## M5 内容与独立信任

### M5-original-content

- **question**: 哪项信息值得补，怎样让人和 AI 都读得懂？
- **principle**: 写有独特价值、有经验支撑、对真人有用的内容。格式可以不同，事实必须同一批。篇幅、FAQ 形状或专用机器文件都不是引用保证。
- **applicable_when**: 代表页缺关键事实、限制、接入步骤或下一步时。
- **actions**: 按现有缺口补原创说明。优先改已有页。Markdown 或其他机器接口可以保留给其他 Agent，但不能当成 Google 引用证明。Google Search 不把 `llms.txt` 当作出现条件。
- **counterexample**: 主要为每个问法变体批量造页；或把有 FAQ 结构本身写成已被引用。
- **acceptance_evidence**: 新增或修改的正文能独立帮人完成任务；机器视图没有多出正文没有的事实。
- **sources**: [Google 生成式搜索优化指南](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide)
- **maturity**: `platform_docs`

### M5-public-sources

- **question**: 读者和 AI 到哪里核验这条陈述？
- **principle**: 公开来源、版本和日期必须能跟随。Schema、摘要和正文说同一件事。第三方引用应独立、相关、可信。
- **applicable_when**: 发布价格、评价、政策、兼容性或任何可核验断言时。
- **actions**: 在正文给出可打开的来源。评价和价格必须有页面上的真实依据。日期写实际变更，不刷日期。
- **counterexample**: 结构化数据写出正文没有的评分；或把作者转述的合同金额当成我们的成效。
- **acceptance_evidence**: 每条对外断言都能跟到公开来源；作者案例没有被写成我们的结果。
- **sources**: [Yao HTML/Schema 合同](https://github.com/yaojingang/yao-geo-skills/blob/201c0c45dcf09bb37bc46a467b4baf4d721db205/skills/yao-geo-page-blueprint/references/schema-html-cms-contract.md)；[姚金刚 2026-09-11 知识库案例](https://x.com/yaojingang/status/2098227639593148422)
- **maturity**: `general_method`

### M5-page-change

- **question**: 这次改了页面上的哪条事实，改前改后各是哪个版本？
- **principle**: 内容修改绑定问题、事实、发布时间、后来的 AI 观察和业务证据。发布旧版不等于已公开新内容。
- **applicable_when**: 本地已改、准备发布或复测时。
- **actions**: 记录改了哪一页、哪些问题和事实、依据是什么。本地改动和公开地址分开。公开后做独立读回。
- **counterexample**: 本地通过测试就写成已上线；或把重新核验旧正文当成发布了新内容。
- **acceptance_evidence**: 每项公开改动有发布时间、读回证据和所绑定的问题或事实。
- **sources**: [Google 发布日期](https://developers.google.com/search/docs/appearance/publication-dates)
- **maturity**: `general_method`

---

## M6 发布、发现与复测

### M6-publish-readback

- **question**: 改动是否已经出现在公开地址上？
- **principle**: 影响回答的公开内容必须在基线之后发布。发布后用公开地址独立读回。本地版本和线上版本不一致时，公开状态不升级。
- **applicable_when**: 声称已发布、已验证或可以开始复测时。
- **actions**: 留下发布时间、发布证据和公开读回。草稿和内部准备可以在基线前做，但不得先改会污染基线的公开正文。
- **counterexample**: 先把答案页全部上线，再补改前采样。
- **acceptance_evidence**: 公开地址上的正文与声称发布的版本一致；读回时间晚于发布时间。
- **sources**: [Google sitemap 说明](https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview)
- **maturity**: `general_method`

### M6-discovery

- **question**: 页面有没有被找到、收录、展示或引用？这些分别是什么证据？
- **principle**: 接收、抓取、索引、展示、引用和推荐分开记录。官方 Google AI 展示量和 Bing 引用量是各自来源行，不能相加，更不是订单来源。
- **applicable_when**: 查看 Search 控制台、Bing 工具或其他官方导出时。
- **actions**: 只用授权导出或产品界面取得官方数据，不写通用抓取器。展示量不足或账号里还没有报告时，记缺口，不编造。
- **counterexample**: 把 AI 展示量和普通搜索展示量相加；或把展示量写成带来了订单。
- **acceptance_evidence**: 每类发现证据单独成行，带来源和窗口；官方数据标明授权导出。
- **sources**: [Google 生成式 AI 展示报告](https://developers.google.com/search/blog/2026/06/gen-ai-performance-reports)；[Bing AI Performance](https://blogs.bing.com/webmaster/February-2026/Introducing-AI-Performance-in-Bing-Webmaster-Tools-Public-Preview)
- **maturity**: `platform_docs`

### M6-retest

- **question**: 同一批问题、同一条件下，回答有没有变化？
- **principle**: 复测必须同题、同平台、同入口、同语言地区。三次是方向观察。列齐检查项不等于证明因果。
- **applicable_when**: 公开改动已经读回，准备比较改前改后时。
- **actions**: 按冻结条件和槽位复测。保留原始回答、全部尝试和不可比情况。未触发的 AI 摘要单列。
- **counterexample**: 反复问到满意后停止；或把 0/3 变 2/3 写成稳定改善或收入因果。
- **acceptance_evidence**: 可比对才写方向变化；不可比的对仍保留，并说明原因。
- **sources**: [Google AI 功能说明](https://developers.google.com/search/docs/appearance/ai-features)
- **maturity**: `general_method`

---

## M7 来源、行为与业务

### M7-touchpoint

- **question**: 这一次访问留下了哪些原始来源信号？
- **principle**: 原始触点与派生渠道分开。实际 referrer、原始 UTM、自己分发的活动、落地页和采集方式分别保留。UTM 可以手填，所以标签命中只证明标签被接收。
- **applicable_when**: 导入访问或注册记录，或解释某次到站时。
- **actions**: 写下时间、站点、落地页版本、原始信号和采集方式。无来源保持未知。测试和自投标签单独标明，不进入自然 AI 引荐。
- **counterexample**: 专属页无来源访问被恢复成 AI；或带 ChatGPT 标签就被写成自然推荐硬证据。
- **acceptance_evidence**: 能解释为什么识别为某渠道；未知、自投和测试没有被升级成自然 AI。
- **sources**: [GA 自定义网址](https://support.google.com/analytics/answer/10917952?hl=en)；[Yao 归因框架](https://github.com/yaojingang/yao-geo-skills/blob/201c0c45dcf09bb37bc46a467b4baf4d721db205/skills/yao-geo-tracking/references/attribution-framework.md)
- **maturity**: `general_method`

### M7-identity

- **question**: 匿名访问、注册和后端事件是不是同一个人，依据是什么？
- **principle**: 只使用授权的显式身份连接。不能仅凭同一页、相近时间或 IP 判断是同一个人。冲突要列出，不能静默覆盖。
- **applicable_when**: 需要用户漏斗、跨事件去重或把访问连到调用和付款时。没有身份时，只报事件量或明示的事件比值。
- **actions**: 记录匿名标识与登录用户的绑定依据。未登录跨设备保持分开。一人多次访问或多次付款，用户转化率不能超过百分之百。
- **counterexample**: 用 IP 或同一文档页把两个访客拼成一人，并据此计算用户付费率。
- **acceptance_evidence**: 身份链有依据；冲突有明细；缺身份时没有冒充用户转化率。
- **sources**: [PostHog 识别用户](https://posthog.com/docs/product-analytics/identify)
- **maturity**: `general_method`

### M7-self-report

- **question**: 用户自己怎么说来的，和浏览器记录有什么不同？
- **principle**: 自报与追踪并存。它们可以描述旅程的不同阶段，不能互相覆盖。自报有记忆偏差，也常常只记得最深的一次。
- **applicable_when**: 表单或回访中询问“最早如何知道”或“这次为何而来”时。
- **actions**: 同时保留“用户说先在 AI 得知”和“这次从 Google 进来”。允许跳过或不记得。只在自报 AI 后追问当时的问题，并留下原话和选择偏差说明。
- **counterexample**: 用自报改写浏览器来源；或把自报金额和追踪金额相加。
- **acceptance_evidence**: 自报和追踪可以同时出现在同一订单上；总额只计算一次。
- **sources**: [Dreamdata 自报试验](https://dreamdata.io/blog/self-reported-attribution-tested)；[PostHog 真实问题实践](https://newsletter.posthog.com/p/llms-are-picking-winners-heres-how)
- **maturity**: `general_method`

### M7-funnel

- **question**: 从到访到注册、调用、付款，走了多少步，分母是什么？
- **principle**: 事件次数和用户或会话漏斗分开。首次成功调用由后端终态证明。没有身份就不能计算用户转化率。
- **applicable_when**: 已有授权业务导出，要说明到访之后发生了什么时。
- **actions**: 分别报告访问、注册、线索、激活、实付和退款的事件数。有身份时再报用户漏斗。业务窗独立于 AI 采样窗。
- **counterexample**: 同一人五次访问、一次注册、三笔付款，却写出超过百分之百的用户转化；或把一次成功调用的前端点击当成终态。
- **acceptance_evidence**: 用户转化不超过百分之百；缺身份时只见事件量或明示事件比值。
- **sources**: [PostHog 漏斗](https://posthog.com/docs/product-analytics/funnels)
- **maturity**: `general_method`

### M7-money-views

- **question**: 这笔钱可以从哪些视角解释，哪个视角也不能加成？
- **principle**: 同一笔实付可以出现在首次可观察来源、本次来源、用户自报和页面接触里。各视角各自去重，总额只算一次，不能相加。现金流按发生期；订单或群体净收款按截至时间。退款跟原订单和原来源走。
- **applicable_when**: 报告关联收入或核对支付导出时。
- **actions**: 待付、失败和测试不计实付。分析记录和支付记录中的同一订单只计一次。未关联退款单列。充值不改称确认收入。金额用主单位，比率写出分子分母。
- **counterexample**: 自报 AI、本次 Google、文档接触和同一笔二十美元订单被加成六十美元；或把 Google AI 展示写成这笔订单的来源。
- **acceptance_evidence**: 各视角可同时保留；用户看到的总额只有一次；没有因果分数时不写增量收入。
- **sources**: [Profound 与 Analytics 关联](https://www.tryprofound.com/blog/google-analytics)；[SearchPilot：SEO 与 GEO 实验不同](https://www.searchpilot.com/geo-a-b-testing-seo-and-geo-are-not-the-same)
- **maturity**: `general_method`

---

## M8 复盘与下一轮

### M8-review

- **question**: 哪项工作值得保留，哪项假设已经被反例打掉？
- **principle**: 对照原来相信什么、做了什么、看到了什么、还有什么解释。工具故障、方法不适用、数据缺失和偶尔有效的步骤要分开处理。作者案例不是我们的成效。
- **applicable_when**: 一轮结束、来源变化，或实践与原文冲突时。
- **actions**: 按 `references/method-evidence.md` 把外部观点、项目假设和反例修订分开记录。来源变了就记下源变化；方法变了就记下方法变化。旧结论保留原文，不改写成“当时就知道”。
- **counterexample**: 一次看起来变好，就把成熟度自动升级；或把厂商文章里的数字当成我们的结果。
- **acceptance_evidence**: 每条建议连到本轮证据或明确缺口；失败可以改规则，成功不自动泛化。
- **sources**: [SearchPilot：SEO 与 GEO 实验不同](https://www.searchpilot.com/geo-a-b-testing-seo-and-geo-are-not-the-same)
- **maturity**: `general_method`

### M8-next-round

- **question**: 下一轮改什么，依据是哪一条证据？
- **principle**: 下一步必须能追溯到本轮证据或缺口。提及率上升本身不是继续扩页的理由。证据不足时，先补正确的数据。
- **applicable_when**: 写下一轮建议，或从候选池挑选新问题时。
- **actions**: 新问题生成新版本，并按比较规则重新取基线。网站基础、内容修改和增量实验按需选择，不默认整站重建。
- **counterexample**: 只因为提到次数增加，就建议再做六张新页；或无合适数据却给出因果分数。
- **acceptance_evidence**: 建议引用具体证据或缺口；小站可以先交描述性案例。
- **sources**: [PostHog 真实问题实践](https://newsletter.posthog.com/p/llms-are-picking-winners-heres-how)
- **maturity**: `general_method`

---

## Related contracts

- Product layers: `references/product-boundary.md`
- Site foundation: `references/site-foundation.md`
- Method evidence kinds: `references/method-evidence.md`
- Method map: `references/method-map.json`
- Review template: `templates/method-review.md`
