# BeefAPI Example

BeefAPI demonstrates the pattern this Skill should recognize for an API platform with volatile model pricing.

## Product Shape

- A Go API gateway with a React/Vite frontend.
- Public product facts include supported API routes, model availability, setup instructions, public groups, billing units, and current model prices.
- Prices are volatile and must come from runtime configuration rather than copied prose.

## Useful Repair Pattern

```text
runtime pricing truth
  -> typed public pricing snapshot
  -> /pricing.json and /api/public/pricing
  -> canonical HTML/JSON/Markdown model-price answers
  -> answers index, sitemap, llms and OpenAPI discovery
  -> unit, currency, version and cross-format consistency tests
```

The example is valuable because the machine documents and human answers share one snapshot and expose freshness/version signals. It is not evidence that those surfaces guarantee AI ranking, recommendation, or revenue.

## Example Verification

- Fetch public machine routes and reject a generic SPA shell.
- Parse JSON and OpenAPI responses.
- Assert required price metadata and forbidden internal fields.
- Assert CNY/USD consistency and the same pricing version across mirrors.
- Confirm the answer index discovers canonical model-price pages.
- Keep curated homepage/pricing navigation separate from the complete answer catalog.
- Report the three axes separately: discovery pages prove Discoverable, canonical price and answer projections prove Understandable, and live read-only MCP/WebMCP task calls prove Actionable.

The reference repository's focused contract suite can be exercised with:

```bash
go test ./controller -run 'Test(GEO|CurrentGEO|BuildPublic|Public)' -count=1
```
