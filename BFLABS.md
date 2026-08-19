# Agent Instructions

This repository is a public, MIT-licensed Agent Readiness Skill Hub. Keep agent
instructions portable: do not add personal paths, private workflow contracts,
customer data, credentials, internal receipts, or organization-only operations.

## Start here

1. For a self-contained code or test task, inspect the relevant implementation
   and tests directly.
2. When the exact owning Skill or canonical document is already known, open it
   directly and skip `docs/INDEX.md`.
3. Use `docs/INDEX.md` only when source ownership or the minimum reading set is
   unclear.
4. Read the root `SKILL.md` for routing behavior and the selected child
   `skills/<name>/SKILL.md` before changing a capability.
5. Read `docs/artifact-protocol.md` before changing schemas, evidence, quality,
   manifests, or output publication.
6. Read `docs/architecture.md` before changing registry, router, orchestrator,
   providers, packaging, or the diagnostic app boundary.

## Invariants

- Route one intent to the smallest capability. Only the two registered workflows
  may execute multiple capabilities automatically.
- Keep Discoverable, Understandable, and Actionable separate from AI visibility
  and business outcome.
- Dynamic facts require a canonical source plus version or capture time.
- Preserve `unknown` and `blocked`; never turn missing evidence into a score or
  factual claim.
- Do not copy AGPL implementation. Follow `THIRD_PARTY_NOTICES.md` and
  `references/licensing-and-attribution.md`.
- Customer production changes, external accounts, real-platform sampling,
  attribution, public deployment, package publication, and release are outside
  ordinary local implementation.

## Verification

Run the checks that match the changed surface. For repository-wide changes, use:

```bash
python3 scripts/skill_registry.py validate
python3 scripts/run_evals.py
npm test --prefix app/readiness-web
npm run check --prefix app/readiness-web
```

Packaging changes also require `python3 scripts/verify_packages.py`. Current
code, schemas, tests, and generated validation receipts outrank plans and prose.
