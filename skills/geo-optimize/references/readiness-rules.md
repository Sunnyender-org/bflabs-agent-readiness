# GEO Readiness Rules

Use these checks to diagnose whether a public product website can state its facts clearly and reproducibly. They measure readiness, not AI ranking.

## 1. Evidence States

| State | Meaning | Treatment |
|---|---|---|
| `pass` | The applicable predicate is proven by current evidence | Record evidence and recheck |
| `fail` | Current evidence disproves the predicate | Produce a bounded repair |
| `unknown` | The evidence is missing or ambiguous | Ask for truth or name the gap |
| `not_applicable` | The product class genuinely lacks the surface | Record the reason; do not penalize |
| `blocked` | Auth, robots, challenge, environment, or access policy prevents inspection | Stop that branch; never fake a score |

## 2. Hard Gates

Treat these as blockers before secondary enhancements:

1. A useful product definition, capability summary, and relevant commercial facts are present in raw or server-rendered HTML—not only after client JavaScript.
2. Public volatile facts have one canonical runtime source plus a freshness signal.
3. Public mirrors do not contradict each other on identity, capabilities, limitations, price, units, currency, availability, or supported routes.
4. Machine-facing URLs return the advertised media type and real content rather than a generic SPA shell or soft 404.
5. The repair does not expose private routes, internal groups, credentials, customer data, unpublished products, or security-sensitive configuration.

## 3. Product Identity

Confirm:

- Canonical product and company names, aliases, old names, and ambiguous names.
- One evidence-backed sentence answering “what is it, for whom, and for what job?”
- Core capabilities and material limitations.
- Canonical public URLs for product, pricing, documentation, setup, status, and contact.
- Consistency between homepage, about/product pages, structured data, and machine documents.

Do not require identical prose everywhere. Require semantic consistency and a clear canonical source.

## 4. Intent Coverage

Sample only commercially or operationally meaningful intents for the product class, usually three to eight:

- What is the product and who is it for?
- How much does it cost, in which unit and currency?
- How do I start or integrate it?
- Which models, plans, regions, platforms, or use cases are supported?
- What are its limitations or unsuitable scenarios?
- How does it compare on a small set of same-basis dimensions?

For each intent, prefer a canonical answer surface with:

- A direct answer near the beginning.
- Evidence-backed facts and dates where needed.
- Boundaries and non-applicable cases.
- A stable URL and canonical metadata.
- A relevant next action.

FAQ formatting is optional. A page earns value from accurate facts and intent fit, not from looking like a FAQ.

## 5. Discovery And Machine Contracts

Inspect applicable surfaces:

- HTTP status, content type, redirect chain, canonical URL, and indexability.
- `robots.txt` intent and sitemap discovery.
- Raw HTML usefulness without JavaScript execution.
- Structured data that parses and matches visible facts.
- `llms.txt` as an optional curated index, not a ranking switch.
- OpenAPI, public catalog, MCP/server cards, pricing JSON, answer JSON, Markdown mirrors, or `/.well-known/*` only when the product actually owns those contracts.

Reject score-gaming artifacts: empty schemas, placeholder endpoints, generic SPA responses, machine documents that advertise nonexistent routes, or duplicated facts that cannot stay current.

## 6. Consistency And Verification

For every volatile or multi-format fact, trace:

```text
authoritative runtime source
  -> public machine response
  -> public human-readable answer
  -> discovery/index surfaces
  -> deterministic consistency checks
```

Verify both the representation and the served result. Prefer one shared projection over hand-maintained copies.

## 7. Conversion Surface

Check only that a useful next action exists and works: register, start, view pricing, read setup, contact sales, or open documentation. Do not infer conversion quality or revenue from CTA presence.

## 8. Agent Actionability Axis

Report Agent Actionability separately from GEO readiness scoring. Inspect stable human fallbacks, WebMCP registration, MCP discovery, typed schemas, tool annotations, representative execution, confirmation boundaries, and result consistency using [agent-actionability.md](agent-actionability.md).

Protocol presence earns no Actionability result by itself. A bridge tag, MCP server card, or `tools/list` response is evidence of discovery, not proof that a useful task completes correctly.

The public Actionable score uses a stable human fallback plus one structured Agent task path. A typed MCP path or a browser-verified WebMCP path can satisfy that second capability; exposing both does not earn duplicate points. Static WebMCP signals remain `present_unverified`, while `not_present` and `not_applicable` do not lower the score by themselves.

## Focused diagnosis

Choose one highest-value next action, grounded in a failed predicate and the affected user task. Prioritize readable, accurate public content over optional markup. Missing JSON-LD alone does not mean missing facts: inspect existing visible and machine-readable facts, then choose only an applicable type. Do not prescribe Organization, SoftwareApplication and Product together by default. Generic infrastructure improvements such as a longer HSTS lifetime are not GEO priorities without a demonstrated access problem.

Distinguish crawler purposes before alleging a conflict. GPTBot controls potential training; OAI-SearchBot serves search discovery. Blocking GPTBot while allowing search or AI input can be intentional and consistent. Read the exact user-agent groups, current provider documentation and actual access evidence; do not auto-unblock training crawlers. References: https://help.openai.com/en/articles/12627856 and https://blog.cloudflare.com/content-signals-policy/ . Usage-purpose signals and crawler access controls are different layers.

A server card, OpenAPI document or tools/list is discovery evidence only. Without a successful representative read-only call and source comparison, describe the action path as found but not verified; do not summarize it as strong or working. A diagnostic HTTP read does not prove tool execution.
