# WebMCP Implementation Patterns

Choose one smallest pattern after inspecting the site's existing interfaces.

## Pattern A: Edge Bridge To Existing Same-Origin MCP

Use when the site already owns a stable MCP endpoint such as `/mcp`.

```text
canonical business truth
  -> existing MCP tools
  -> same-origin /mcp
  -> edge-injected WebMCP bridge
  -> visitor browser Agent
```

This is the preferred Cloudflare path. Do not duplicate tool handlers in frontend JavaScript. Verify that the bridge uses the intended same-origin endpoint and that the MCP endpoint remains directly usable without the bridge.

## Pattern B: Native Browser Tool Registration

Use when the website owns a small set of page-local actions and no reusable MCP server exists.

- Register against the browser's supported `modelContext` surface.
- Use stable names, concise descriptions, explicit JSON schemas, and truthful annotations.
- Delegate to existing page/domain functions rather than reimplementing business rules.
- Return typed, bounded results and preserve normal UI fallbacks.
- Dispose registrations on page lifecycle changes when the browser API requires it.

## Pattern C: MCP Server Plus Native Compatibility Adapter

Use when a canonical MCP server exists but some environments need direct native registration.

- Keep the MCP server as truth.
- Generate or adapt browser tools from MCP descriptors.
- Contract-test name, schema, annotation, and result parity.
- Do not let adapter-specific names drift from the server without an explicit compatibility map.

## Reject These Patterns

- Tool handlers that scrape the site's own DOM when a canonical data/API function exists.
- Separate hard-coded price, inventory, plan, availability, or capability logic in the browser.
- A WebMCP-only action with no human or direct API/MCP fallback.
- Tool discovery documents that advertise unavailable endpoints.
- Generic proxy tools that expose arbitrary internal routes or caller-supplied URLs.
