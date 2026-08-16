# Licensing And Attribution

## Repository license

The repository is MIT licensed. Runtime code, schemas, fixtures, tests, Skill instructions, and documentation added by BFLabs must be compatible with MIT distribution.

## Clean-room rule for GEOHub

GEOHub is AGPL-3.0-only. BFLabs may study its public architecture and independently implement general ideas such as capability registries, bounded workflows, evidence ledgers, quality reports, and artifact manifests. Contributors must not copy GEOHub code, schemas, templates, tests, synthetic fixtures, or substantial documentation text into this repository.

This repository uses its own names, field definitions, implementation, tests, examples, and prose. A design resemblance is not sufficient provenance: every submitted file must be explainable from this repository's confirmed plan, existing BFLabs behavior, a public standard, or a separately compatible source.

## Compatible references

- GEO Citation Lab: MIT for software and Skill assets; CC BY 4.0 for original reports, documentation, visualizations, and catalog metadata; third-party materials retain their own licenses.
- Yao GEO Skills: MIT.
- qiaomu-seo: MIT.
- Waza: MIT.

Copying substantial MIT material still requires preservation of its copyright and license notice. Research claims must cite their source and retain platform, sample, causal, and limitation boundaries.

## Packaging gate

Public packages must exclude `.receipts`, `runs`, customer inputs, local environments, absolute user paths, secrets, tokens, private analytics, and undeclared third-party material. Files declaring AGPL, GPL, proprietary, or unknown source licenses fail the distribution gate unless the repository license and release boundary are explicitly reconsidered by the owner.
