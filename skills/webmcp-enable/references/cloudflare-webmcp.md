# Cloudflare WebMCP Developer Preview

Use this route only when the target zone is already proxied through Cloudflare and the user explicitly authorizes the exact production setting change.

## Enable Sequence

1. Open the verified Cloudflare account and zone.
2. Go to `Agent Readiness -> Labs`.
3. Read the current WebMCP state and available packs.
4. Enable WebMCP for the exact approved domain.
5. Enable only `Site MCP Server` by default.
6. Keep Content Credentials/C2PA and future packs off unless separately justified and approved.
7. Confirm the Site MCP Server URL is same-origin `/mcp`, or record the explicit approved alternative.

Do not infer cost, stable-browser support, or production SLA from developer-preview availability. Read current Cloudflare pricing and limitations before any paid or capacity-sensitive test.

## Deterministic Readback

Check the served HTML, not only the dashboard state:

```bash
curl -sS https://example.com/ | grep -F '/.webmcp/bridge.js'
```

Then validate the advertised MCP endpoint, `tools/list`, expected schemas and annotations, and representative read-only calls.

## BrowserRun Verification

- Use a Lab session with current WebMCP-compatible Chrome.
- Navigate to the real domain.
- List WebMCP tools on every relevant page load.
- Execute only the approved read-only task plan.
- Re-list after a state-changing navigation because available tools may change.
- Save tool descriptors, task results, capture time, canonical fact version, and failures.

A lab-session creation receipt is not task success. A tool-list receipt is not useful-task success.

## Rollback Sequence

1. Disable the `Site MCP Server` pack or WebMCP switch for the exact domain.
2. Fetch served HTML and confirm the edge bridge is absent.
3. Confirm the canonical `/mcp` and human website remain available.
4. Record rollback time and reason.
