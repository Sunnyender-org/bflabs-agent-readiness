# Artifact Protocol 1.0.0

Every successful deterministic run publishes one atomic directory:

```text
run-*/
├── input/request.json
├── evidence-ledger.json
├── quality-report.json
├── run-manifest.json
└── outputs/*
```

The manifest binds the input hash, capability or workflow, status, degradation, external gates, output media types, schemas, and SHA-256 for every artifact. A modified artifact fails replay validation.

## Evidence rules

- Every factual claim uses one or more evidence IDs.
- Dynamic facts require a canonical source plus `fact_version` or capture time.
- Missing evidence remains `unknown`; blocked access remains `blocked`.
- AI visibility and business outcome remain `not_measured` unless their own evidence contract is satisfied.
- Markdown outputs are hashed and validated like JSON outputs.

## Quality report

The quality report separates warnings from blockers. A warning may publish a degraded but honest run, such as zero valid measurement samples. A blocker prevents atomic publication, such as stale dynamic facts used as current, an unsupported ranking claim, a manifest mismatch, or a path escaping the run directory.

## Download envelope

The diagnostic app downloads an `artifact-pack.schema.json` envelope containing the manifest and its JSON files. The envelope is a transport representation of the same protocol, not a new report format. Consumers must validate the manifest and recompute hashes before trusting any file.
