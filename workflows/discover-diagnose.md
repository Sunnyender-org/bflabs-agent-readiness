# discover-diagnose

Use only when the request explicitly asks to discover audience questions or opportunities before diagnosing a brand, site, or page.

```text
geo-discover
  -> query-map.json
  -> opportunity-map.json
  -> evidence link
geo-optimize
  -> readiness-report.json
```

Both steps publish in one atomic Artifact Protocol run. Failure in either step prevents a partial workflow from being represented as complete.
