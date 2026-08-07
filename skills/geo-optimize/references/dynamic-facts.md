# Dynamic Facts

Read this reference when the website publishes prices, plans, inventory, model availability, exchange rates, quotas, limits, service status, regional support, or any fact likely to change.

## Canonical Source Pattern

Use one runtime truth owner and derive every public representation from it:

```text
runtime configuration or database
  -> typed public projection
  -> JSON/API response
  -> HTML/Markdown answer page
  -> sitemap or discovery index
```

Avoid copying current values into several files. Static prose may explain the pricing model, but current numbers should come from the canonical projection.

## Minimum Public Metadata

Expose the applicable fields:

- `schema_version`
- `generated_at` or `effective_at`
- a content/version hash or monotonic version
- canonical source URL
- item/product/model identifier and display name
- billing or measurement unit
- currency and conversion basis where relevant
- public audience, plan, or group semantics
- cache lifetime or refresh expectations
- explicit unknown/not-applicable states

Do not expose internal cost, margin, channel ownership, private group identifiers, supplier secrets, or credentials merely because they exist in the runtime model.

## Pricing Checks

For pricing, verify:

1. Human and machine surfaces use the same runtime snapshot.
2. Input/output/cache/image/audio/fixed-price units cannot be confused.
3. Currency pairs are mathematically consistent within declared rounding tolerance.
4. Public plan/group multipliers are explained without leaking private upstream configuration.
5. Missing price is distinguished from zero price and unsupported billing mode.
6. The page identifies when the value was generated and where to recheck it.

## Repair Strategy

- Prefer a small typed projection module over controller/page-specific formatting.
- Reuse it for JSON, HTML, Markdown, structured data, and tests.
- Add contract tests for required fields, forbidden private fields, units, currency conversions, and cross-format version equality.
- Add a live or local HTTP smoke only after deterministic unit/contract checks exist.

Stop if publishing the fact itself is a product decision or if no authoritative source exists.
