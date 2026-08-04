# Framework Mapping

Read only the section matching the detected repository. Use existing project conventions before these generic patterns.

## React/Vite SPA

Typical failure: crawlers receive only an app shell for product, pricing, answer, or machine-document paths.

Preferred repairs, from smallest to largest:

1. Serve real static files directly from `public/` for JSON, Markdown, `llms.txt`, OpenAPI, sitemap, and well-known contracts.
2. Add server-rendered or pre-rendered HTML for a bounded set of high-value answer pages.
3. Reuse the same data module in the interactive UI and the static/server projection.
4. Consider broader SSR/SSG migration only after an explicit architecture decision.

Do not treat a client-side route that returns the same root HTML as a valid answer page.

## Next.js Or Similar SSR/SSG Frameworks

- Prefer static generation for stable answer pages.
- Use server rendering or revalidation for volatile facts.
- Emit canonical metadata and structured data from the same typed source as visible content.
- Confirm the raw response contains the answer before hydration.

## Go HTTP/Gin With A Separate Frontend

- Put canonical public fact projection in a service/domain module, not in each controller.
- Serve machine formats through explicit backend routes with correct content types.
- Serve canonical HTML answer pages from the backend or a build-time generated bundle when the SPA cannot provide raw content.
- Keep router-to-controller-to-service boundaries consistent with the repository.
- Test the real router and response body, not only helper functions.

## Static Site Generators

- Generate answer pages, sitemap entries, structured data, and machine mirrors from one content/fact source.
- Fail the build on duplicate slugs, invalid schemas, missing canonical URLs, or inconsistent versions.

## Closed CMS Or No Writable Repository

Audit and produce a manual change map. Do not pretend the Agent can implement or verify CMS changes without an approved connector and real readback.
