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

- **Copy to Agent**: the primary result action copies a self-contained prompt with the scan fingerprint, one selected child Skill, stable site-hosted Skill URLs, verification requirements, and no-deploy boundary;
- **Agent Journey**: runs a deterministic enter-understand-continue task from the same public responses. It is supporting readiness evidence only and never changes a score or measurement layer;
- **Opt-in leaderboard**: off by default. When explicitly selected, it stores only the domain, three axes, scan time, and fingerprint summary;
- **Download Artifact Pack**: downloads the protocol manifest, input, evidence ledger, quality report, and canonical readiness report with SHA-256 hashes;
- **Save baseline and retest**: keeps one baseline in page memory, reruns the same public target, and displays a three-axis Before / After comparison without mixing in AI visibility or business outcome;
- **Contact BFLabs**: opens the public `hello@bflabs.cn` inquiry route with the target, scan fingerprint, readiness results, and requested paid-delivery lane prefilled.

The root and child Skills are served through a fixed allowlist and a SHA-256-bound `/.well-known/agent-skills/index.json`. The same report is available through the versioned API, `text/markdown`, packaged `bflabs-readiness scan` CLI, and Streamable HTTP MCP tools.

The free surface covers public diagnosis, the open-source Skill, local changes, and in-session retesting. The paid surface covers customer repository/CMS/infrastructure implementation, repeated real-platform sampling, monitoring, and customer-authorized business attribution. The email route starts a service conversation; it is not an automated checkout or proof that paid delivery operations are complete.

The scanner remains a bounded six-path audit. Agent Journey uses those responses and may follow at most one selected same-origin public link to prove continuation. It does not execute page instructions, submit forms, log in, or crawl the full site. WebMCP can be `present_unverified` but cannot become verified compatible-browser task completion here.

## Compatibility and verification

Node tests cover SSRF and redirect safety, readiness semantics, shared report topology, and Artifact Pack hashes. The repository Python suite validates a Node-generated report, ledger, quality report, and manifest against the same JSON Schemas used by CLI runs.

Manual local regression is performed at desktop width and 360px. Controls are semantic links/buttons, include visible keyboard focus, and remain at least 44px high. The evidence table scrolls inside its own container on narrow screens.

## Safety status

This build rejects credentials, unsupported schemes and ports, IP literals, unsafe DNS results, and unsafe redirects. It caps redirects and response bodies and does not forward cookies, authorization, or referrers.

The Worker build uses Cloudflare `global_fetch_strictly_public`, rejects literal/private-style targets and unsafe ports, applies separate client and target rate-limit bindings, caps request/response bodies and redirects, uses per-fetch timeouts, and honors `/.well-known/bflabs-agent-readiness-opt-out`. Full reports stay in the browser. An optional `LEADERBOARD` KV binding stores only explicitly opted-in public summaries; without that binding, scans still succeed and publication reports `unavailable`. Cloudflare observability is enabled for operational errors. Passing local smoke or a dry run does not prove a live deployment; use the canonical release checklist for live state.

```bash
npm run build:worker
npx wrangler deploy --config wrangler.jsonc
```
