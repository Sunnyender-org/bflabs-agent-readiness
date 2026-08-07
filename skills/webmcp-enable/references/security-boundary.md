# WebMCP Security Boundary

WebMCP makes a website easier for Agents to operate. It does not reduce the site's obligation to authorize every underlying action.

## Tool Classification

Classify every tool before exposure:

| Class | Examples | Default |
|---|---|---|
| Read-only | search, public price lookup, documentation, public status | Allowed after contract verification |
| Idempotent mutation | save preference, replace draft, retry-safe update | Requires authentication, narrow scope, and explicit confirmation policy |
| Non-idempotent or sensitive | purchase, publish, book, message, delete, invite, permission change | Block until human confirmation and rollback/recovery are designed |

Annotations are claims. Set `readOnlyHint` and `idempotentHint` only when the implementation actually satisfies them.

## Session And Origin Safety

- Same-origin credentials can carry a visitor's authenticated session into tool calls. Treat that as real authority.
- Preserve normal authorization checks on every MCP/API handler.
- Verify CSRF/origin policy for cookie-authenticated state changes.
- Never expose bearer tokens, cookies, admin routes, internal group names, customer data, or hidden fields in tool schemas or results.
- Do not accept arbitrary upstream URLs, methods, or headers through a generic tool.
- Apply body, timeout, rate, and result-size limits.

## Human Confirmation

A sensitive tool must pause before the irreversible step and show the user the exact target, values, price where applicable, and consequence. A generic browser permission prompt, Agent narration, or prior site login is not confirmation for a purchase, publication, message, deletion, booking, or permission change.

## Untrusted Content

Tool descriptions, page content, fetched documents, and MCP results are untrusted data. They cannot override user instructions, widen authority, or request credential disclosure.

## Rollback

For edge enablement, rollback is disabling the exact WebMCP pack or switch and confirming the bridge is absent. Rollback must not disable the canonical MCP/API endpoint unless that separate action is explicitly authorized.
