# Contributing

Thank you for improving BFLabs Agent Readiness. This repository accepts evidence-bounded changes to the root router, six child Skills, two stable workflows, schemas, deterministic providers, tests, and the local diagnostic app.

## Before changing behavior

1. Keep Discoverable, Understandable, and Actionable independent.
2. Keep AI visibility and business outcome outside readiness scores.
3. Preserve `unknown` and `blocked`; do not convert missing evidence into a fact or score.
4. Bind volatile facts to a canonical source and a version or capture time.
5. Do not add a third stable workflow without a public design discussion and registry migration.
6. Do not copy GEOHub implementation, schemas, templates, tests, or prose into this MIT repository. See `THIRD_PARTY_NOTICES.md`.

## Development loop

```bash
python3 -m pip install -e '.[dev]'
bflabs-readiness validate
bflabs-readiness eval
npm test --prefix app/readiness-web
npm run check --prefix app/readiness-web
python3 scripts/verify_packages.py
```

Add or update deterministic fixtures for behavior changes. Tests must cover success, missing evidence, dynamic-fact staleness, blocked external gates, forbidden claims, and package leak boundaries when applicable.

## Pull requests

Describe the changed contract, evidence, degradation behavior, tests, and any external gate. Do not include credentials, customer inputs, raw production receipts, private paths, or revenue data. A passing local suite is not approval to deploy the scanner or perform external actions.
