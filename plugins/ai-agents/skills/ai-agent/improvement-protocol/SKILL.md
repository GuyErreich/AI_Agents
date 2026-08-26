---
name: improvement-protocol
description: Flags and implements improvements to skills, rules, and agent instructions. Use when discovering patterns that should be documented, after any task that surfaces a reusable gap, or when updating `skills/` or `rules/`.
disable-model-invocation: true
---

# Improvement Protocol

When a new improvement is discovered during development or review, **flag it before implementing doc changes**. Non-blocking doc work goes in **separate parallel sessions**.

**Canonical location:** this plugin's `skills/ai-agent/improvement-protocol/SKILL.md` ([GuyErreich/AI_Agents](https://github.com/GuyErreich/AI_Agents)) — do not duplicate per project.

## When to flag

- Code pattern or rule would benefit if documented
- Existing instruction is incomplete or outdated
- New architectural or UI pattern should be standardized
- Skill or rule needs expansion
- Fix addresses a **class of defect** (clip boundary, dismiss lifecycle, RLS pattern) — even on first occurrence

## Mandatory post-task flag block

After completing a task — especially when a reusable pattern, class-of-bug, or instruction gap showed up, or when editing skills or rules — end the task with:

```markdown
## Improvement flags
- [none]
```

or one or more flags using the template below.

**Flagging is automatic.** **Implementing** doc/skill changes still requires user approval (parallel session recommended) unless the user explicitly asked to update skills in the same task.

## Flag template

```markdown
🔧 IMPROVEMENT FLAGGED:

**Category:** [Skills | Rules | Agents]
**Target File:** [path/to/file.mdc or SKILL.md]
**Title:** [Concise name]
**Description:** [What to add/change and why]
**Scope:** [Single file | Multiple files | New file]
**Portable or project:** [portable this plugin `skills/foundations/**` or `skills/code/**` | project `<repo>/.cursor/skills/project/**` | plugin `rules/**`]
**Estimated Effort:** [Quick | Medium | Complex]
**Priority:** [Nice-to-have | Recommended | Critical]
```

## Process

1. **Flag** explicitly with context (mandatory block above)
2. **Ask:** implement now, parallel session (recommended), or skip
3. **Parallel session:** read target file, draft, implement, validate, report back
4. Main session continues uninterrupted

## Good vs skip

**Good:**

- Pattern appears 2+ times
- Clarifies ambiguity or standardizes naming
- **Class-of-bug** — reusable category (overflow clip vs padding, overlay dismiss lifecycle, boundary validation)
- Documents edge cases agents will hit again

**Skip:**

- One-off typo or single-instance data bug
- Contradicts existing style
- Massive refactor required
- Speculative features

## Target files

| Layer | Path |
|---|---|
| System behaviors | this plugin `rules/behaviors/*.mdc` |
| Portable foundations rules | this plugin `rules/foundations/**/*.mdc` |
| Portable foundations skills | this plugin `skills/foundations/**/SKILL.md` |
| Portable ai-agent rules | this plugin `rules/ai-agent/**/*.mdc` |
| Portable ai-agent skills | this plugin `skills/ai-agent/**/SKILL.md` |
| Portable code rules | this plugin `rules/code/**/*.mdc` |
| Portable skills | this plugin `skills/code/**/SKILL.md` |
| Project skills | `<repo>/.cursor/skills/project/**/SKILL.md` |
| Project rules | `<repo>/.cursor/rules/project/*.mdc` |
| Agent entry | `<repo>/AGENTS.md`, `AGENT.md` chain |
| CI only | `.github/workflows/` (not agent context) |

Keep portable `foundations/**`, `code/**`, and `ai-agent/**` skills free of project paths and commands. Project-specific guidance belongs in `project/**` or the repo `AGENT.md` chain.

## Portable vs project (quick rule)

| If the lesson is… | Put it in… |
|---|---|
| Generic web UX / layout pattern | this plugin `skills/code/web/ux/references/` |
| App shell tokens, component names, tab mapping | Repo `AGENT.md` or future project skill |
| Supabase / Postgres | Repo `project/platform/supabase` |
