# Documentation Index

This index routes maintainers and agents to the owning source. It is not a
second product plan or release receipt.

## Task reading matrix

| Task | Must read | Read when relevant |
| --- | --- | --- |
| Route a request or change capability selection | `../SKILL.md`, `../references/routing.md` | `../registry/capabilities.json`, routing evals |
| Change one child capability | `../skills/<name>/SKILL.md` | Its referenced templates, schemas, providers and tests |
| Change a workflow | `../workflows/<name>.md`, `architecture.md` | Both child Skills, workflow schemas and end-to-end tests |
| Change artifacts, evidence, quality or manifests | `artifact-protocol.md`, `architecture.md` | JSON Schemas, compatibility fixtures and replay tests |
| Change the diagnostic app | `architecture.md`, app README/source | SSRF, redirect, schema, download and UI checks |
| Change packaging or installation | `install-codex-claude.md`, `release-checklist.md` | Packaging allowlists, manifests, license and isolated-install tests |
| Review product boundary or licensing | `../references/product-boundary.md`, `../references/licensing-and-attribution.md` | `../THIRD_PARTY_NOTICES.md`, `../SECURITY.md` |
| Resume the v1 refactor history | `agent-readiness-v1-progress.md` | `agent-readiness-v1-complete-refactor-plan.md` and master goal as historical delivery context |
| Prepare a public release | `release-checklist.md` | Current git state, clean package build and explicit maintainer approval |

## Source ownership

- `SKILL.md` files own natural-language behavior and capability boundaries.
- Registry and schemas own machine-readable contracts.
- `artifact-protocol.md` owns evidence and publication invariants.
- Tests and validation receipts own local verified state.
- `agent-readiness-v1-progress.md` records the dated local release-candidate
  projection; it does not prove a current public release.
- GitHub releases and package registries, when they exist, own published state.

## Freshness

Plans and goals explain intent and delivery history. Before making a current
claim, check code, tests, package metadata, and the relevant external system.
Never infer publication, deployment, AI visibility, ranking, recommendation, or
business outcome from local readiness checks.
