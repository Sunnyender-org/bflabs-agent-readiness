# BFLabs Agent Readiness Web

Local promotion-candidate app inside the `bflabs-agent-readiness` monorepo. It is a UI over the same Artifact Protocol and `readiness-report.schema.json` used by the Python CLI, not a second scoring system.

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
- **Copy Agent optimization prompt**: copies an evidence-bounded handoff that preserves unknown states and owner gates;
- **Contact BFLabs / view repository**: uses the public GitHub organization repository as the confirmed contact path.

The scanner remains a bounded six-path audit. It does not crawl the full site or run a compatible-browser task, so WebMCP can be `present_unverified` but cannot become `verified` here.

## Compatibility and verification

Node tests cover SSRF and redirect safety, readiness semantics, shared report topology, and Artifact Pack hashes. The repository Python suite validates a Node-generated report, ledger, quality report, and manifest against the same JSON Schemas used by CLI runs.

Manual local regression is performed at desktop width and 360px. Controls are semantic links/buttons, include visible keyboard focus, and remain at least 44px high. The evidence table scrolls inside its own container on narrow screens.

## Safety status

This build rejects credentials, unsupported schemes and ports, IP literals, unsafe DNS results, and unsafe redirects. It caps redirects and response bodies and does not forward cookies, authorization, or referrers.

It is not approved for public deployment. A production scanner still needs DNS pinning/rebinding protection, per-client and per-target rate limits, durable abuse controls, opt-out policy, bounded retention, and an independent security review. Passing this local smoke does not authorize deployment.
