# De-identified BeefAPI readiness case

This example preserves the public method while removing customer, request, finance, traffic, and production-operation details.

## Situation

An AI API gateway had public product pages, a dynamic pricing endpoint, an `llms.txt`, a sitemap, and read-only MCP tools for model discovery, pricing lookup, group comparison, cost calculation, and integration guidance.

## Diagnosis

- Discoverable: public HTML and machine indexes were available.
- Understandable: product definition and dynamic pricing were explicit, with a pricing version.
- Actionable: typed same-origin MCP tools existed, but browser-native WebMCP was not proven.
- AI visibility: not measured by the readiness scan.
- Business outcome: not measured by the readiness scan.

## Open-source actions

The local workflow can audit the fixed public paths, route failed predicates, create a price-answer page blueprint from versioned facts, and aggregate user-supplied model-answer observations. It cannot claim that those changes caused ranking, citation, conversion, or revenue.

## Commercial seam

Repeated real-platform sampling, compatible-browser task verification, CMS or infrastructure implementation, monitoring, and customer-authorized attribution remain separately scoped services with their own permissions and receipts.
