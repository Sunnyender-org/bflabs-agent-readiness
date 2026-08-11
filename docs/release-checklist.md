# Public release candidate checklist

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

## Owner gates

- [ ] Ender separately approves commit.
- [ ] Ender separately approves push and target branch.
- [ ] Ender separately approves GitHub release or package publication.
- [ ] Public diagnostic deployment receives its own security, privacy, abuse, rate-limit, retention, and DNS-rebinding review.

Completing this checklist locally produces a release candidate only. It never implies that commit, push, release, package upload, or deployment occurred.

Local verification on 2026-08-11: 50 Python tests, 9 Node tests, 62/62 router cases, zero forbidden misroutes, 100% workflow precision, two isolated Python installs, six extracted child Skills, and two isolated workflow runs passed. The 62-case router suite p95 was 127.146 ms; 20 deterministic workflow runs had p95 27.115 ms and max 28.435 ms. These timings exclude package installation and external network scanning.
