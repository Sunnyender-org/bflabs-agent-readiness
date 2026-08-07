# Agent Readiness UI design

Minimal CF-style prototype built with `@bflabs/ui`.

## Surfaces

1. **Landing** — headline + single URL field + check
2. **Report** — three axes + findings; Skill / paid behind “如何改进”
3. **Delivery** — staged Before/After example (optional tab)

## Run

```bash
# requires local bflabs-ui package build
cd ../../../bflabs-ui/packages/ui && pnpm build

cd designs/bflabs-ui-agent-readiness
pnpm install
./node_modules/.bin/vite --port 5188 --host 127.0.0.1
```

Visual source of truth: [Sunnyender-org/bflabs-ui](https://github.com/Sunnyender-org/bflabs-ui)

Preview screenshots: `preview/01-diagnose.png`, `02-report.png`, `03-delivery.png`
