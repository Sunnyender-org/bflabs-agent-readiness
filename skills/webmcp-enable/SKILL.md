---
name: webmcp-enable
description: Audit, implement, explicitly enable, and verify WebMCP for an existing website with a stable browser or MCP fallback. Use when exposing typed website actions to browser Agents, bridging an existing same-origin MCP server through Cloudflare WebMCP, adding native modelContext tools, or running real BrowserRun task verification. Not for GEO indexing claims, crawler optimization, write-capable tools without human confirmation, hidden admin APIs, credential extraction, automatic production changes, or replacing the canonical MCP/API with an experimental browser bridge.
---

# WebMCP Enable

Make an existing website safely actionable by browser Agents. Preserve the site's canonical API or MCP surface, add the smallest suitable WebMCP adapter, and prove representative tasks through a real compatible browser.

Contract version: `0.1.0`.

## Relationship To GEO

- `geo-optimize` audits whether the website is Discoverable and Understandable, and reports Agent Actionability as a separate axis.
- `webmcp-enable` owns the implementation and verification of the Actionable axis.
- WebMCP does not prove that ChatGPT, Gemini, Perplexity, or a search engine indexed, cited, recommended, or converted the site.

## Select The Mode

- **Audit**: inspect repository and served-site evidence without changing anything.
- **Implement**: add or repair repository-local MCP/WebMCP code after explicit local-change authorization.
- **Enable**: change a real Cloudflare or equivalent site setting only after explicit authorization for that exact domain and pack.
- **Verify**: discover tools and execute an approved read-only task plan in a compatible browser or BrowserRun session.

An unqualified request defaults to Audit. Never infer production Enable authority from Implement authority.

## Workflow

1. Read the nearest repository instructions, dirty state, framework, public routes, existing MCP/API contracts, authentication boundaries, and deployment topology.
2. Read [implementation-patterns.md](references/implementation-patterns.md) and choose one smallest pattern. Prefer an existing same-origin MCP endpoint over duplicating business logic in browser code.
3. Read [security-boundary.md](references/security-boundary.md). Inventory each proposed tool as read-only, idempotent, or mutating. Stop on unresolved write/session/permission behavior.
4. In Cloudflare mode, read [cloudflare-webmcp.md](references/cloudflare-webmcp.md). Keep `Site MCP Server` as the only default pack unless another pack has an explicit use case and approval.
5. Implement only the chosen adapter. Keep the canonical MCP/API directly usable when the WebMCP bridge is absent or unsupported.
6. Verify deterministic contracts first: server card, endpoint media type, initialize when required, `tools/list`, JSON schemas, annotations, and bounded `tools/call` results.
7. Run a real compatible-browser task plan. Re-list tools after state changes. Compare volatile results with the canonical public source and preserve the fact version or captured time.
8. Return the receipt below. Do not claim success from a dashboard toggle, injected tag, tool list, or submitted Agent prompt alone.

## Cloudflare Enable Gate

Before changing Cloudflare, name and verify:

- exact account and zone;
- exact domain;
- current WebMCP state;
- enabled pack set;
- MCP URL, defaulting to same-origin `/mcp` only when verified;
- rollback action;
- post-change HTML and BrowserRun checks.

Enable only the approved pack set. A developer preview must remain additive and reversible.

## Verification Floor

A verified result requires:

1. Served HTML exposes the expected WebMCP bridge or native registration in a compatible browser.
2. The Agent discovers the expected tools with names, descriptions, input schemas, and truthful annotations.
3. Every task in the approved plan returns a terminal result.
4. Read-only results match canonical public facts within declared freshness/version rules.
5. Failures preserve the task, tool, arguments classification, response state, and exact gap.
6. Unsupported browsers retain a functional human or direct MCP/API fallback.

Use [task-plan.json](templates/task-plan.json) and [verification-receipt.json](templates/verification-receipt.json) when artifacts are requested. The bundled `scripts/verify_site_mcp.py` verifies same-origin MCP contracts and approved read-only task calls; real BrowserRun verification remains a separate required receipt.

## Output Contract

Return:

1. Mode, repository scope, domain, account/zone when applicable, and adapter pattern.
2. Canonical API/MCP truth and fallback path.
3. Tool inventory with read-only/idempotent/mutating classification.
4. Files and external settings changed.
5. Deterministic contract results.
6. Real-browser task results with fact version, captured time, and failure receipts.
7. Rollback path and residual preview/browser limitations.
8. `AI visibility: not measured` and `Business outcome: not measured` unless separately proven.

## Abort Conditions

Stop before implementation or enablement when the authoritative action source is missing, a proposed tool exposes private/admin behavior, write tools lack human confirmation, the current account/zone/domain cannot be verified, authentication is unavailable, the MCP endpoint contradicts the advertised server card, or the external action exceeds the user's exact authorization.
