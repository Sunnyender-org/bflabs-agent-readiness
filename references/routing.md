# Routing

## Route to `geo-optimize`

Use `skills/geo-optimize/SKILL.md` when the requested outcome is repository-local:

- audit public facts, answer pages, schema, sitemap, robots, or `llms.txt`;
- repair volatile pricing or other machine-readable facts;
- check Agent Actionability without implementing WebMCP;
- verify approved GEO changes.

## Route to `webmcp-enable`

Use `skills/webmcp-enable/SKILL.md` when the requested outcome includes:

- native WebMCP registration;
- connecting a same-origin MCP server to WebMCP;
- enabling Cloudflare WebMCP or a tool pack;
- compatible-browser or BrowserRun tool discovery and task calls;
- security review of browser Agent tools.

External enablement and production mutations are explicit-only. A local audit does not authorize them.

## Route to the diagnostic app

Use `app/readiness-web` only for bounded, read-only inspection of public fixed paths. Treat its score as an evidence index, not a ranking or business score.

## Do not route here

- generic SEO, backlink purchasing, or bulk content;
- real-platform ranking guarantees;
- hidden admin or permission mutation exposure;
- autonomous payment or credential handling;
- conversion or revenue attribution without customer-authorized data.
