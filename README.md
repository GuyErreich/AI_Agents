# AI Agents

Portable [Cursor](https://cursor.com) plugin: skills, rules, subagents, and review-loop hooks. Project-specific overlay (Supabase, deploy secrets, `AGENT.md`) stays in each application repo.

Plugin: [`plugins/ai-agents`](plugins/ai-agents)

## Install in Cursor

### Local (this machine)

```bash
mkdir -p ~/.cursor/plugins/local
ln -sfn "$(pwd)/plugins/ai-agents" ~/.cursor/plugins/local/ai-agents
```

Reload the Cursor window. The plugin shows up as **AI Agents**.

### Team marketplace

1. Cursor **Dashboard → Settings → Plugins**
2. **Team Marketplaces → Import from Repo**
3. Paste `https://github.com/GuyErreich/AI_Agents`

Cursor reads [`.cursor-plugin/marketplace.json`](.cursor-plugin/marketplace.json). Mark **AI Agents** required or optional, then save.

### Public marketplace

Submit the repo at [cursor.com/marketplace/publish](https://cursor.com/marketplace/publish).

## Layout

```
.cursor-plugin/marketplace.json   # GitHub / team import
plugins/ai-agents/
  .cursor-plugin/plugin.json
  skills/                         # foundations, code, ai-agent
  rules/                          # glob + always-on pointers
  agents/                         # pr-reviewer, pr-fixer
  hooks/                          # review-loop + npm dep gate
```

## Consuming repos

Keep only the project overlay:

```
AGENT.md tree
.cursor/skills/project/**
.cursor/rules/project/**
scripts/review-lock.py            # optional
```

Do not copy portable `skills/code/**` or `rules/code/**` into app repos once this plugin is installed — they would load twice.

## Inheritance

Every skill under `code/` extends `skills/code/foundations/engineering`. Folder taxonomy lives in `skills/foundations/hierarchy`. Agent-library container tiers live in `skills/ai-agent/hierarchy`. Project skills may add stricter rules, never weaker ones.
