# Install for Codex and Claude Code

Each child package is a ZIP whose top-level directory is the Skill name. Inspect `PACKAGE_MANIFEST.json`, `LICENSE`, and `THIRD_PARTY_NOTICES.md` before installation.

## Codex

OpenAI documents repository Skills under `$REPO_ROOT/.agents/skills/<skill-name>/SKILL.md` and personal Skills under `$HOME/.agents/skills/<skill-name>/SKILL.md`. Codex detects changes automatically, with restart as a fallback. See [OpenAI: Build skills](https://developers.openai.com/codex/skills).

Project-scoped installation:

```bash
mkdir -p .agents/skills
unzip geo-optimize-0.4.1.zip -d .agents/skills
```

Install only the smallest Skill needed. To expose the root router and all capabilities as one Python CLI, install the unified wheel instead:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install bflabs_agent_readiness-0.4.1-py3-none-any.whl
.venv/bin/bflabs-readiness list --status active --format markdown
```

## Claude Code

Anthropic documents project Skills under `.claude/skills/<skill-name>/SKILL.md` and personal Skills under `~/.claude/skills/<skill-name>/SKILL.md`. See [Anthropic: Extend Claude with skills](https://docs.anthropic.com/en/docs/claude-code/skills).

Project-scoped installation:

```bash
mkdir -p .claude/skills
unzip geo-optimize-0.4.1.zip -d .claude/skills
```

The Skill frontmatter and portable references are shared. OpenAI-specific `agents/openai.yaml` metadata is ignored by Claude Code; it does not change the Skill instructions.

## Verify before use

```bash
python3 scripts/verify_packages.py
```

Package verification checks allowlists, hashes, licenses, private paths, token-shaped strings, child entrypoints, a clean wheel install, the router eval, and both stable workflows. It does not authorize external accounts, production changes, publishing, or deployment.
