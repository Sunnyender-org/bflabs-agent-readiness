# Public release candidate checklist

Last live readback: 2026-08-23

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
- [x] The primary result action copies a self-contained Agent prompt tied to the scan fingerprint and one site-hosted child Skill; Artifact Pack download remains a separate advanced action.
- [x] A report can be saved as an in-page baseline and compared with a same-site retest.
- [x] The UI keeps readiness, AI visibility, and business outcome separate during comparison.
- [x] Free self-service and paid BFLabs delivery boundaries are explicit.
- [x] The BFLabs inquiry action uses the public `hello@bflabs.cn` route and includes the target, fingerprint, and readiness snapshot.
- [x] The local post-release Agent handoff selects one evidence-backed repair Skill and does not require BFLabs to prove that a customer deployed a proposed change.
- [x] A local private delivery prototype separates portable engagement truth from its WorkBuddy command host and rejects unsupported measured states in synthetic contract tests.
- [x] The local report includes a deterministic enter-understand-continue Agent Journey that explicitly cannot change readiness, AI visibility, or business outcome.
- [x] The local web UI, versioned API, Markdown projection, packaged CLI, and MCP scan tool use the same report contract.
- [x] The local opt-in leaderboard defaults off, stores summary-only records for at most 30 days, and discloses its three-axis ordering without creating a combined score.
- [x] The root and all six child Skills are exposed through a SHA-256-bound Agent Skills index; the local BF Labs Skills catalog lists GEO as a SkillHub host using stable site URLs.
- [ ] Before / After can be downloaded as one schema/hash-valid comparison artifact.
- [ ] Paid delivery has auditable real-platform sampling, monitoring, implementation, and attribution runbooks/receipts.

## GitHub live state

- [x] v1 implementation commit `8bd65d428d4e67b3fdc1334ba32efce72695baaf` exists on `agent/complete-agent-readiness-v1`.
- [x] Follow-up commit `12458a1cffed6d037e6b6f35425cea343462a737` was pushed to the PR branch and both PR checks passed.
- [x] PR [#1](https://github.com/Sunnyender-org/bflabs-agent-readiness/pull/1) merged as `7aa7b9e1e366b795c4d0e0d523f60bdc24c85185`.
- [x] GitHub Release [`v0.3.0`](https://github.com/Sunnyender-org/bflabs-agent-readiness/releases/tag/v0.3.0) is published from the merge commit.
- [x] The release contains source, unified wheel, and all six child-Skill packages with GitHub SHA-256 digests.
- [x] Email follow-up commit `dd87282c4b453bbf76904d68c0e4ee870bf5f6f9` is on `main`; Actions run `31961670907` passed.
- [x] Productization PR [#4](https://github.com/Sunnyender-org/bflabs-agent-readiness/pull/4) merged as `8cebb0801f9cb809d50716d61fc424945e74522e`; both checks passed.
- [x] GitHub Release [`v0.4.0`](https://github.com/Sunnyender-org/bflabs-agent-readiness/releases/tag/v0.4.0) was published from that merge commit with eight uploaded assets and GitHub SHA-256 digests.
- [x] SkillHub metadata PR #5 merged as `e32788a0e0a5a672d0c898589f6d3387700bcd4a`; Release `v0.4.1` and Worker `e9ab84ad-34df-4301-b8d7-5439c3b41235` were published.
- [x] The 0.4.1 source asset was withdrawn before any download after package audit found local `.wrangler` and generated `.worker-build` files; the seven unaffected wheel/child assets remain available.
- [x] Package-hygiene PR #6 merged as `5677a2824fee281ffc17d4b9dc4b69e2e08d30fa`; Release [`v0.4.2`](https://github.com/Sunnyender-org/bflabs-agent-readiness/releases/tag/v0.4.2) contains nine assets, including a 68-file SkillHub ZIP and a source archive with generated/runtime state excluded.
- [x] Icon-binding PR #7 merged as `fa2ae364dcc909707fb8b503c6f269660e1d8265`; Release [`v0.4.3`](https://github.com/Sunnyender-org/bflabs-agent-readiness/releases/tag/v0.4.3) contains nine uploaded assets with GitHub SHA-256 digests.

## Production live state

- [x] [readiness.bflabs.cn](https://readiness.bflabs.cn) is a separate Cloudflare Worker custom domain and does not replace the apex website.
- [x] Homepage, privacy page, and ruleset API return HTTPS 200.
- [x] A production loopback-literal scan is rejected with 400.
- [x] A production `https://beefapi.com` scan returned `100 / 100 / 75`, Artifact Pack `pass`, AI visibility `not_measured`, and business outcome `not_measured`.
- [x] `hello@bflabs.cn` routes to the email Worker; the owner destination is verified and a real smoke message was received.
- [ ] Lucas's destination is verified and a real dual-inbox delivery is confirmed; Cloudflare sent a fresh verification email on 2026-08-23 and the current state is `pending`.
- [x] Prompt-first UI, Agent Journey, versioned API/Markdown/CLI/MCP, Agent Skills index, and leaderboard are deployed and read back from production.
- [x] Production Worker version `f626760b-73c3-4332-9b9e-1a48381ed44e` binds `LEADERBOARD`; default-private and explicit opt-in behavior, share page, remote key, and 30-day expiration were read back.
- [x] `bflabs-skills` PR #3 merged as `b46ec827d47b0da880053b98230b155b87442ed1`; Worker `ea9d6bb1-9724-43a0-bb4b-163cf2d6b12e` serves the updated GEO entry and four public catalog pages.
- [x] External SkillHub lists `@user_49f8ec71/bflabs-agent-readiness` at approved version 0.4.3; public search and both detail URLs resolve, and the dashboard icon URL was visually verified as the BFLabs logo.

## Owner gates

- [x] Ender approved committing and pushing the 2026-08-17 follow-up to `agent/complete-agent-readiness-v1`.
- [x] Ender approved PR merge.
- [x] Ender approved GitHub Release and package publication.
- [x] Ender approved public diagnostic deployment without replacing the existing `bflabs.cn` website.
- [x] Ender approved provisioning the leaderboard storage binding and deploying the 2026-08-22/23 productization worktree.
- [x] Ender approved deploying the local BF Labs Skills catalog changes.
- [x] Ender approved the external SkillHub submission under the target platform account, including the BFLabs logo.

## Public diagnostic safety gate

- [x] Production fetch uses Cloudflare `global_fetch_strictly_public`; literal IP, private-style hostnames, unsafe ports and unsafe redirects are rejected.
- [x] Per-client and per-target Cloudflare rate-limit bindings are configured and included in deployment dry-run.
- [x] Request/response caps, redirect limits, subrequest timeouts and Cloudflare observability are configured; local Worker smoke passed.
- [x] Target opt-out and a response path for abuse reports exist.
- [x] Full reports, evidence bodies, prompts, and IP addresses are not stored; only explicitly opted-in leaderboard summaries may enter the KV binding, with a 30-day TTL.
- [ ] An independent security review has signed off the public scanner design and implementation.

The checked GitHub and production items above are live readbacks, not inferences from local tests. The remaining unchecked items stay open.

The checked 2026-08-18 private paid-delivery prototype remains local only: it has not been installed in WorkBuddy, connected to a customer account, or used for a real paid engagement. Public diagnostic, GitHub release, Skills catalog, and SkillHub listing receipts are complete where checked above; they do not prove a paid customer pilot, AI visibility, or business outcome.

Latest local verification on 2026-08-17: 50 Python tests, 18 Node/Worker tests, Node syntax checks, Worker build and Cloudflare dry-run, 62/62 router cases, zero forbidden misroutes, and 100% workflow precision passed. Package verification passed for source, unified, and all six child Skills, including two isolated Python installs and both workflow runs. Release `v0.3.0` was rebuilt from the merge commit and its eight artifacts were uploaded with GitHub digests.

Latest local verification on 2026-08-23: 55 Python tests, 31 Node/Worker tests, 62/62 router cases, repository/Skill validators, Worker build, OpenAPI JSON, CLI live scan, Markdown, MCP, Agent Skills index, opt-in leaderboard and server-rendered share pages, 30-day KV retention, desktop/390px browser checks, and BF Labs Skills catalog syntax/render passed. Package verification passed with 200 source files, 157 unified-wheel files, a 68-file SkillHub package, all six child packages, two isolated installs, and both workflow runs.

A real 2026-08-23 production scan of `https://beefapi.com` returned `100 / 100 / 75`, Agent Journey `pass`, AI visibility `not_measured`, and business outcome `not_measured`; the report still requires a compatible-browser task before WebMCP can become verified.

The 2026-08-11 release-candidate receipt remains historical evidence for router p95 `127.146 ms` and deterministic workflow p95 `27.115 ms` / max `28.435 ms`. Re-run package verification after any further source change and again from the exact commit selected for publication.
