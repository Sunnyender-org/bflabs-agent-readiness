# discover-content

Use only when the request explicitly asks to discover audience questions or opportunities before producing one of the seven content modes.

```text
geo-discover
  -> query-map.json
  -> opportunity-map.json
  -> content-spec.discovery_context
geo-content
  -> content-spec.json
  -> content.md
```

Every factual claim remains evidence-linked. Dynamic facts must pass freshness checks, and publication remains an owner gate.
