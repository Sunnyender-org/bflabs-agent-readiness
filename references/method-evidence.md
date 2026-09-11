# Method evidence

Agent-only. Teaching, Skills, and reports may quote the Chinese sentences. This file does not store product prices, models, or customer facts.

A method claim can be one of three records. Keep them separate. Do not promote one kind into another because the wording is confident.

## Three record kinds

### 1. External view

别人怎么说。官方文档、作者方法、厂商文章或转述案例都属于这一类。

Write down: who said it, when, where, the claim in their words, what we adopt, and what we refuse to copy.

作者的案例不是我们的成效。厂商文章里的流量、合同金额或满意度，不能写成我们的结果，也不能变成字数或收费指标。

Example that must stay an external view:

- 姚金刚 2026-09-11 提到某服务商整理知识库后，内容和合同都让客户满意。这是作者转述，没有我们核过的客户、合同或测量。可采用的方向是先理清企业事实，再写对真人也有用的内容。不得把字数或合同金额当成方法验收。

### 2. Project hypothesis

我们准备这样试，但还没有被本项目的证据证实或反驳。

Write down: the hypothesis, why it is needed now, what would support it, what would refute it, and the current maturity (`project_hypothesis`).

一次看起来变好，不能自动升级成熟度。

Example that must stay a project hypothesis until measured:

- 首个实践站是 `https://global.beefapi.com/`。面向英文开发者时，先看首页、一张价格或产品页、一张接入文档是否够用。这不是已证明的最佳页数，也还没有本文件可填写的采样结果。

### 3. Counterexample revision

实践、核对或反例说明：原来的说法不成立，或适用条件必须收窄。

Write down: what we used to believe, what we saw, which source changed, which method changed, and how the old sentence is preserved. Use maturity `revised` only on the method entry that actually changed.

来源变化和方法变化要分开记。不能把旧记录改写成“当时就知道”。

Example of a revision that is not a customer result:

- 曾有执行稿假设：答案页不进人类导航，落地本身更能证明 AI 来源。核对后的方法是：页面服务正常读者；可以放在文档或帮助中心，不必挤进顶部菜单；公开地址仍可能从搜索、转发或书签进入；缺来源保持未知。这是对未采用假设的修订，不是某个站点已经获客。

## Practice may refute a method

When later evidence conflicts with a method step:

1. Keep the original method sentence and its date.
2. Add a review using `templates/method-review.md`.
3. Record the source change if the cited document moved, disappeared, or was corrected.
4. Record the method change if the principle, condition, or action is now different.
5. Point `references/method-map.json` at the same method ID. Do not silently edit old case records to match the new rule.

工具故障就修工具，并留下能复现的反例。方法不适用就改适用条件或撤回结论，不要为了保住方法而换样本。数据缺失就补可观察环节，不能把未知写成无效，也不能估成收入。

## What each kind may support

| Kind | May support | Must not become |
| --- | --- | --- |
| external view | wording, caution, a cited official rule | our traffic, our revenue, our case study |
| project hypothesis | this project's next action and its untested boundary | platform_docs, case_observation, or a guarantee |
| counterexample revision | a narrower condition or a withdrawn step | a claim that the old case already used the new rule |

Small sites may stop at a descriptive case. Do not invent a causal score to make the record look complete.

## Related contracts

- Method prose: `references/whitehat-method.md`
- Pointers: `references/method-map.json`
- Review form: `templates/method-review.md`
