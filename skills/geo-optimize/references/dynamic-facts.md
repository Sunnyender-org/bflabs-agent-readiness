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

## Three time types

Do not collapse these timestamps:

- **Effective** (`effective_at`): when this value became true for customers. A scheduled price change uses the moment it takes effect, not the moment someone later checked it.
- **Verified** (`verified_at` or `last_reviewed_at`): when a person or job last compared the public surface to the canonical source. Re-verify does not mean the body changed.
- **Content-updated** (`content_updated_at` or the page's real last-updated date): when the public HTML, Markdown, or equivalent body actually changed.

`generated_at` is only the clock time of a projection render. It is not a content-updated date and not proof the business fact changed.

Publishing an old snapshot is not publishing new content. Answering a current-price question with an old price is still currently inaccurate, even if the page still shows the old value and an old date.

## Minimum Public Metadata

Expose the applicable fields:

- `schema_version`
- `effective_at` for when the value became true
- `verified_at` only when a check happened
- `content_updated_at` or an equivalent last-updated date only after the public body changed
- `generated_at` when a projection was rendered, kept separate from the three times above
- a content/version hash or monotonic version
- canonical source URL
- item/product/model identifier and display name
- billing or measurement unit
- currency and conversion basis where relevant
- public audience, plan, or group semantics
- cache lifetime or refresh expectations
- explicit unknown/not-applicable states

Do not expose internal cost, margin, channel ownership, private group identifiers, supplier secrets, or credentials merely because they exist in the runtime model. Do not copy current prices or models into method docs; they belong in the project fact record.

## Pricing Checks

For pricing, verify:

1. Human and machine surfaces use the same runtime snapshot.
2. Input/output/cache/image/audio/fixed-price units cannot be confused.
3. Currency pairs are mathematically consistent within declared rounding tolerance.
4. Public plan/group multipliers are explained without leaking private upstream configuration.
5. Missing price is distinguished from zero price and unsupported billing mode.
6. The page identifies the effective time, the last verified time, and the last content-updated time as different fields, and where to recheck the value.
7. A later verification without a body change leaves content-updated unchanged.

## Repair Strategy

- Prefer a small typed projection module over controller/page-specific formatting.
- Reuse it for JSON, HTML, Markdown, structured data, and tests.
- Add contract tests for required fields, forbidden private fields, units, currency conversions, and cross-format version equality.
- Add a live or local HTTP smoke only after deterministic unit/contract checks exist.

Stop if publishing the fact itself is a product decision or if no authoritative source exists.
