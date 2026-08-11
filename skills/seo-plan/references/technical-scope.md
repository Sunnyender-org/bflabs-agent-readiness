# Technical SEO Scope

## Separate controls

- Crawl permission in `robots.txt` does not replace meta robots or `X-Robots-Tag` indexing controls.
- Canonical, redirects, sitemap membership, and hreflang must be checked as related but separate signals.
- Sitemap and IndexNow improve discovery signaling but do not guarantee crawl or index state.
- Structured data must match visible facts; validation does not guarantee presentation features.
- Core Web Vitals lab and field observations remain separate evidence types.
- Named search and AI crawlers must be evaluated by documented purpose, not merged into one “AI bot” switch.

## Evidence and action boundary

No supplied evidence means `unknown` plus an acquisition step, not a failed finding. A confirmed failed observation may produce an implementation action, but each action remains `owner-approval-required` and includes captured pre-state, bounded verification, and rollback.

Official source hashes and capture times prove which guidance snapshot informed the plan. Recheck stale sources before implementation.
