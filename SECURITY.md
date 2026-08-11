# Security policy

## Supported surface

The open-source release candidate covers local Skills, a deterministic Python CLI, offline fixtures, and a local fixed-path diagnostic app. The app is not approved as a public multi-tenant scanner.

## Reporting a vulnerability

Open a private security advisory in the GitHub repository. Do not include live credentials, customer data, or exploit traffic against third-party systems. If a private advisory is unavailable, open a minimal issue asking maintainers for a private reporting route without disclosing the vulnerability.

## Scanner boundary

The local scanner rejects credentials in URLs, unsupported schemes and ports, IP literals, unsafe DNS results, unsafe redirects, oversized bodies, cookies, authorization, and referrers. A public deployment still requires DNS pinning and rebinding protection, per-client and per-target rate limits, abuse controls, opt-out, bounded retention, privacy review, and an independent security assessment.

## Agent boundary

Open Skills may inspect public or user-provided evidence and create local plans or artifacts. They do not authorize login bypass, private-console access, production mutation, Cloudflare changes, Search Console actions, publishing, payments, platform sampling, or business attribution. Each such action requires a separate owner gate and a verifiable receipt.
