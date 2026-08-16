# BFLabs Agent Readiness Web

Diagnostic app inside the `bflabs-agent-readiness` monorepo. It is a UI over the same Artifact Protocol and `readiness-report.schema.json` used by the Python CLI, not a second scoring system. It can run as the local Node prototype or as the bounded Cloudflare Worker build.

It reports three independent axes:

- Discoverable: public pages and machine entry points are reachable.
- Understandable: product facts and volatile facts are explicit, current, and consistent.
- Actionable: an Agent has a discoverable task path through links, WebMCP, MCP, or typed public tools.

It does not measure AI visibility, ranking, citation, recommendation, conversion, or revenue. Missing evidence stays `unknown`; it is never converted into a failed check or a numeric score.

## Run

```bash
bun test
bun run check
bun run start
```

Open `http://127.0.0.1:4177` and scan a public domain.

## Report contract

The scan response keeps the legacy `axes` array, evidence rows, scan metadata, findings, and compatibility fields used by the prototype. Its canonical `readiness_report` object validates against the shared schema and contains:

- the three readiness axes;
- evidence-linked verification predicates;
- `ai_visibility: not_measured` and `business_outcome: not_measured`;
- explicit external verification gates.

The page displays failed predicates, evidence gaps, bounded opportunities, and the smallest relevant child Skills. It also provides:

- **Download Artifact Pack**: downloads the protocol manifest, input, evidence ledger, quality report, and canonical readiness report with SHA-256 hashes;
- **Hand off to Agent**: downloads the Artifact Pack and copies an evidence-bounded prompt tied to the scan fingerprint, unknown states, minimum child-Skill routes, owner gates, and required Before / After rerun;
- **Save baseline and retest**: keeps one baseline in page memory, reruns the same public target, and displays a three-axis Before / After comparison without mixing in AI visibility or business outcome;
- **Contact BFLabs**: opens the public `hello@bflabs.cn` inquiry route with the target, scan fingerprint, readiness results, and requested paid-delivery lane prefilled.

Child-Skill links are served from the current checked-out repository through a fixed allowlist. A controlled preview therefore does not depend on the Draft PR already being merged into GitHub `main`.

The free surface covers public diagnosis, the open-source Skill, local changes, and in-session retesting. The paid surface covers customer repository/CMS/infrastructure implementation, repeated real-platform sampling, monitoring, and customer-authorized business attribution. The email route starts a service conversation; it is not an automated checkout or proof that paid delivery operations are complete.

The scanner remains a bounded six-path audit. It does not crawl the full site or run a compatible-browser task, so WebMCP can be `present_unverified` but cannot become `verified` here.

## Compatibility and verification

Node tests cover SSRF and redirect safety, readiness semantics, shared report topology, and Artifact Pack hashes. The repository Python suite validates a Node-generated report, ledger, quality report, and manifest against the same JSON Schemas used by CLI runs.

Manual local regression is performed at desktop width and 360px. Controls are semantic links/buttons, include visible keyboard focus, and remain at least 44px high. The evidence table scrolls inside its own container on narrow screens.

## Safety status

This build rejects credentials, unsupported schemes and ports, IP literals, unsafe DNS results, and unsafe redirects. It caps redirects and response bodies and does not forward cookies, authorization, or referrers.

The Worker build uses Cloudflare `global_fetch_strictly_public`, rejects literal/private-style targets and unsafe ports, applies separate client and target rate-limit bindings, caps request/response bodies and redirects, uses per-fetch timeouts, keeps reports in the browser instead of an application database, and honors `/.well-known/bflabs-agent-readiness-opt-out`. Cloudflare observability is enabled for operational errors. Passing local smoke or a dry run does not prove a live deployment; use the canonical release checklist for live state.

```bash
npm run build:worker
npx wrangler deploy --config wrangler.jsonc
```
