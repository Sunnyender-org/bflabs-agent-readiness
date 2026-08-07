# BFLabs Agent Readiness Web

Local promotion-candidate app inside the `bflabs-agent-readiness` monorepo.

It reports three independent axes:

- Discoverable: public pages and machine entry points are reachable.
- Understandable: product facts and volatile facts are explicit, current, and consistent.
- Actionable: an Agent has a discoverable task path through links, WebMCP, MCP, or typed public tools.

It does not measure AI visibility, ranking, citation, recommendation, conversion, or revenue.

## Run

```bash
bun test
bun run check
bun run start
```

Open `http://127.0.0.1:4177` and scan a public domain.

## Safety status

This build rejects credentials, unsupported schemes and ports, IP literals, unsafe DNS results, and unsafe redirects. It caps redirects and response bodies and does not forward cookies, authorization, or referrers.

It is not approved for public deployment. A production scanner still needs DNS pinning/rebinding protection, per-client and per-target rate limits, durable abuse controls, opt-out policy, bounded retention, and an independent security review.
