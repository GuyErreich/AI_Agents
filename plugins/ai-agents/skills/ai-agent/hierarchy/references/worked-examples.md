# Worked Examples (Agent Library)

Illustrations of container-tier and aggregation decisions. Folder nesting still follows `foundations/hierarchy`.

## 1. Quality vs language — deepen vs mislabel

**Candidates:** `code/quality/performance`, `code/quality/security` under `code/languages/nodejs`.

Generic cleanup/security rules fail the nesting test for Node — they hold for any runtime. Keep them under `quality/`. Node-only env-prefix or npm tooling belongs as a `references/` file under `languages/nodejs`, not by moving whole quality skills.

**Rule applied:** deepen the language skill with a reference; do not widen by nesting universal quality under a runtime.

## 2. CI milestone skills — short skills vs parent references

**Candidates:** `code/ci/{commit,pr,push,local-review-loop}` and behavior rules `git-commit-consent`, `git-push-consent`.

- Each milestone has its own trigger and workflow → separate `SKILL.md` files are justified (step 3 of aggregation decision).
- Repeated `git-*` prefixes on consent rules are a latent grouping signal; introduce `ci/git/` or `behaviors/git/` only when **3+** siblings share that context.
- If a milestone skill stayed tiny with no references and was always loaded with siblings, it would be a candidate to become a `references/` file of a parent `ci` skill — that is the open question for further flattening.

**Rule applied:** new skill when trigger/workflow differ; earn folder levels; watch for short-skill → reference demotion.

## 3. `meta` → `ai-agent` — rename applied

**Was:** `skills/meta/improvement-protocol`.  
**Now:** `skills/ai-agent/improvement-protocol` (and this `ai-agent/hierarchy` skill).

- `meta` named the abstraction level, not the subject a newcomer searches for.
- Retrieval test favored `ai-agent`. Rename-for-drift was applied in the same change as this skill; indexes updated together.

**Rule applied:** subject-named parent for agent-stack maintenance; couple hierarchy + improvement protocol under one change unit.

## 4. `code/web/ux` references — subfolders are fine, chains are not

**Candidate:** `code/web/ux/references/{desktop,mobile,shared}/` plus two top-level references.

| Check | Result |
|---|---|
| Does `SKILL.md` link each file directly? | Yes — the `## When to load references` table names all nine paths |
| Does any group hold 3+ files on one axis? | `shared/` has 4, `mobile/` has 2, `desktop/` has 1 |
| Is any reference reachable only through another reference? | No |

Verdict: **keep the subfolders.** They also let `desktop/navigation-motion.md` and `mobile/navigation-motion.md` share a filename that reads correctly under its parent — flattening would force prefixes for no gain. `desktop/` sitting at one file is the only soft signal; it stays because the viewport axis is already routed and a second desktop reference is expected.

**Rule applied:** link depth is the constraint, not folder depth. A flatten-everything rule would have caused churn and lost the axis in the path.
