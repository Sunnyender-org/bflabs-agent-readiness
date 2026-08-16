# Public release candidate checklist

Last live readback: 2026-08-17

## Contract

- [x] Registry exposes the root plus exactly six active child Skills.
- [x] Workflow registry exposes exactly `discover-diagnose` and `discover-content`.
- [x] Unknown and blocked states remain unscored and unpromoted.
- [x] Dynamic facts have canonical evidence plus version or time.
- [x] AI visibility and business outcome remain separate from readiness.

## Verification

- [x] Repository validator passes in the local release-candidate worktree.
- [x] Router eval accuracy is at least 95%, forbidden misroutes are zero, workflow precision is 100%.
- [x] Python, Node, schema, compatibility, SSRF, redirect, measurement, and packaging tests pass.
- [x] Source, unified, and six child packages pass allowlist validation.
- [x] Source tarball and unified wheel install in separate new virtual environments; the unified wheel completes both workflows.
- [x] All packages contain MIT license and third-party notices.
- [x] Package scan reports zero private paths, receipts, user data, credentials, or internal operational data.
- [ ] Human provenance review confirms no GEOHub AGPL implementation was copied.

## Product trial loop

- [x] A report can be downloaded as a schema/hash-bound Artifact Pack.
- [x] One action downloads the Artifact Pack and copies an Agent handoff tied to its scan fingerprint.
- [x] A report can be saved as an in-page baseline and compared with a same-site retest.
- [x] The UI keeps readiness, AI visibility, and business outcome separate during comparison.
- [x] Free self-service and paid BFLabs delivery boundaries are explicit.
- [x] The BFLabs inquiry action uses the public `hello@bflabs.cn` route and includes the target, fingerprint, and readiness snapshot.
- [ ] Before / After can be downloaded as one schema/hash-valid comparison artifact.
- [ ] Paid delivery has auditable real-platform sampling, monitoring, implementation, and attribution runbooks/receipts.

## GitHub live state

- [x] v1 implementation commit `8bd65d428d4e67b3fdc1334ba32efce72695baaf` exists on `agent/complete-agent-readiness-v1`.
- [x] The branch is pushed and Draft PR [#1](https://github.com/Sunnyender-org/bflabs-agent-readiness/pull/1) is open.
- [x] PR #1 is `MERGEABLE` / `CLEAN`; both recorded `validate / repository` checks are `SUCCESS`.
- [ ] PR #1 is merged.
- [ ] A GitHub Release exists.
- [ ] A source, unified, or child-Skill package is uploaded to a public distribution surface.

The current 2026-08-17 follow-up changes are still local and are not part of PR head `8bd65d4`.

## Owner gates

- [x] Ender approved committing and pushing the 2026-08-17 follow-up to `agent/complete-agent-readiness-v1`.
- [x] Ender approved PR merge.
- [x] Ender approved GitHub Release and package publication.
- [x] Ender approved public diagnostic deployment without replacing the existing `bflabs.cn` website.

## Public diagnostic safety gate

- [x] Production fetch uses Cloudflare `global_fetch_strictly_public`; literal IP, private-style hostnames, unsafe ports and unsafe redirects are rejected.
- [x] Per-client and per-target Cloudflare rate-limit bindings are configured and included in deployment dry-run.
- [x] Request/response caps, redirect limits, subrequest timeouts and Cloudflare observability are configured; local Worker smoke passed.
- [x] Target opt-out and a response path for abuse reports exist.
- [x] The app has no report/input database; privacy and terms pages describe the runtime boundary.
- [ ] An independent security review has signed off the public scanner design and implementation.

Completing local checks produces a release candidate only. It never implies that the current worktree was committed or pushed, that the Draft PR was merged, or that a release, package upload, paid service operation, or deployment occurred.

Latest local verification on 2026-08-17: 50 Python tests, 16 Node/Worker tests, Node syntax checks, Worker build and Cloudflare dry-run, 62/62 router cases, zero forbidden misroutes, and 100% workflow precision passed. Local Worker smoke returned 200 for the UI, privacy page, ruleset and a real `https://beefapi.com` scan, while rejecting a literal loopback target with 400. Package verification also passed for source, unified, and all six child Skills, including two isolated Python installs and both workflow runs. Those builds were temporary verification artifacts, not uploaded packages; final publication hashes must be generated from the exact approved commit.

A real local scan of `https://beefapi.com` returned three readiness axes at 100/pass and an HTTP 200 Artifact Pack; the report still marks WebMCP `present_unverified`, requires compatible-browser task verification, and keeps AI visibility/business outcome `not_measured`.

The 2026-08-11 release-candidate receipt remains historical evidence for router p95 `127.146 ms` and deterministic workflow p95 `27.115 ms` / max `28.435 ms`. Re-run package verification after any further source change and again from the exact commit selected for publication.
