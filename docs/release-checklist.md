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
- [x] Follow-up commit `12458a1cffed6d037e6b6f35425cea343462a737` was pushed to the PR branch and both PR checks passed.
- [x] PR [#1](https://github.com/Sunnyender-org/bflabs-agent-readiness/pull/1) merged as `7aa7b9e1e366b795c4d0e0d523f60bdc24c85185`.
- [x] GitHub Release [`v0.3.0`](https://github.com/Sunnyender-org/bflabs-agent-readiness/releases/tag/v0.3.0) is published from the merge commit.
- [x] The release contains source, unified wheel, and all six child-Skill packages with GitHub SHA-256 digests.
- [x] Email follow-up commit `dd87282c4b453bbf76904d68c0e4ee870bf5f6f9` is on `main`; Actions run `31961670907` passed.

## Production live state

- [x] [readiness.bflabs.cn](https://readiness.bflabs.cn) is a separate Cloudflare Worker custom domain and does not replace the apex website.
- [x] Homepage, privacy page, and ruleset API return HTTPS 200.
- [x] A production loopback-literal scan is rejected with 400.
- [x] A production `https://beefapi.com` scan returned `100 / 100 / 75`, Artifact Pack `pass`, AI visibility `not_measured`, and business outcome `not_measured`.
- [x] `hello@bflabs.cn` routes to the email Worker; the owner destination is verified and a real smoke message was received.
- [ ] Lucas's destination is verified and a real dual-inbox delivery is confirmed.

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

The checked GitHub and production items above are live readbacks, not inferences from local tests. The remaining unchecked items stay open.

Latest local verification on 2026-08-17: 50 Python tests, 18 Node/Worker tests, Node syntax checks, Worker build and Cloudflare dry-run, 62/62 router cases, zero forbidden misroutes, and 100% workflow precision passed. Package verification passed for source, unified, and all six child Skills, including two isolated Python installs and both workflow runs. Release `v0.3.0` was rebuilt from the merge commit and its eight artifacts were uploaded with GitHub digests.

A real production scan of `https://beefapi.com` returned `100 / 100 / 75` and Artifact Pack `pass`; the report still marks WebMCP `present_unverified`, requires compatible-browser task verification, and keeps AI visibility/business outcome `not_measured`.

The 2026-08-11 release-candidate receipt remains historical evidence for router p95 `127.146 ms` and deterministic workflow p95 `27.115 ms` / max `28.435 ms`. Re-run package verification after any further source change and again from the exact commit selected for publication.
