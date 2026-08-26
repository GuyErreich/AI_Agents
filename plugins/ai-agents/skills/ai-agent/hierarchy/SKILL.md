---
name: agent-hierarchy
description: Agent-library hierarchy — when to add a rule, SKILL.md, reference, or asset; link depth vs folder depth; prefer deepening over widening. Use when creating or reorganizing skills, rules, or AGENT.md under .cursor/ or the agent stack. Extends foundations/hierarchy.
disable-model-invocation: true
---

# Agent Hierarchy

How to organize an **agent library** (skills, rules, `AGENT.md`). In a source tree the main aggregation lever is a parent folder. In an agent library aggregation is usually a `references/` file: context budget punishes eager loading, and every new skill folder adds a discovery surface.

**Prefer deepening an existing skill over widening the tree.**

## Extends

Load `skills/foundations/hierarchy/SKILL.md` first. Nesting and retrieval tests apply; this skill adds **container tiers** and agent-specific aggregation.

## Container tiers (context cost, low → high)

| Tier | When | Cost |
|---|---|---|
| `rules/*.mdc` `alwaysApply: true` | Tiny triggers and pointers needed on nearly every request | Highest — every turn |
| `rules/*.mdc` with `globs` | Domain entry when matching files are open | High when open |
| `SKILL.md` | One coherent workflow or domain; keep well under 500 lines | Medium — on attach / load |
| `references/<topic>.md` | Depth most tasks do not need | Low — load on demand |
| `references/<group>/<topic>.md` | 3+ references share a real axis **and** `SKILL.md` routes to each file explicitly | Low |
| `assets/` | Copyable templates, images, data files — **never documentation** | On copy only |
| `AGENT.md` chain | Project-local context by path proximity | When working in that folder |

## Link depth, not folder depth

The constraint is how many hops the agent takes to reach a file, not how deep the folder is.

- **`SKILL.md` links directly to every reference.** Never require reading one reference to discover another — chained references risk partial reads.
- **Folder depth under `references/` is unconstrained.** A subfolder is fine when it carries a real axis and `SKILL.md` routes to its files by name.
- Cross-skill pointers (`see code/web/libs/react/references/gsap-patterns.md`) are "see also" hints, not load paths — the owning skill still links its own references directly.

## Aggregation decision

Run **before** choosing any new folder:

1. Does an existing skill already own this responsibility? → Add `references/<topic>.md`; do **not** create a sibling skill.
2. Needed on nearly every task and expressible in one to three lines? → Make it a rule (prefer glob over always-on).
3. Has its own trigger and workflow, and loading it would drag in unrelated context? → New skill.
4. Multiple references share an axis? → Stay flat with filename prefixes until the group reaches **3+ files**; then a `references/<group>/` folder is justified. Add the routing table in the same change.

Then apply the nesting and retrieval tests from `foundations/hierarchy` to the chosen path.

## Agent drift signals

Load `references/worked-examples.md` for illustrations. Restructure when:

| Signal | Action |
|---|---|
| `SKILL.md` past ~500 lines | Split into `references/`, not sibling skills |
| Reference reachable only by reading another reference | Link it directly from `SKILL.md` |
| `references/<group>/` holding 1–2 files | Flatten with a filename prefix |
| Subfolder exists with no routing table in `SKILL.md` | Add the routing table or flatten |
| Documentation living in `assets/` | Move to `references/` |
| References always loaded together | Merge them |
| A reference never loaded | Summary sufficed — fold or delete |
| Two skills with identical `Extends` always loaded together | Merge |
| Short skill, no references, shares axis with siblings | Candidate to become a `references/` file of a parent skill |
| Always-applied rule past ~10 lines | Move body to a skill; keep a pointer rule |

## When to load references

| Topic | Reference |
|---|---|
| Agent taxonomy worked examples | `references/worked-examples.md` |
