# Restructure Playbook

How to fix a folder tree that started one way and grew into another. Load only when drift signals appear or a move is planned.

## Drift signals

| Signal | What it usually means |
|---|---|
| Hesitation where to file a new item | Axis at that level is unclear or mixed |
| Sibling names share a repeated prefix (`git-commit`, `git-push`) | A grouping folder is latent; names are simulating it |
| Every item only makes sense with one qualifier | Contents are domain-bound; parent name is too generic or wrong |
| Cross-references constantly reach sideways | Wrong nesting — related change units are split across parents |
| Folder name no longer describes contents | Rename-for-drift, or split generic from specific |

## Six operations

| Operation | When to use |
|---|---|
| **Nest (demote)** | Nesting test passes for a real parent; items belong under shared context |
| **Hoist (promote)** | Nesting test fails — item is meaningful outside its current parent |
| **Split generic / specific** | Folder mixes universal rules with domain-bound rules; keep generic high, move specifics under the domain |
| **Merge** | Two folders share one axis and one change unit; retrieval is better as one path |
| **Rename for drift** | Name describes abstraction level or history (`meta`) instead of the subject (`ai-agent`) |
| **Flatten** | A level has one long-term occupant and adds no retrieval value — collapse the chain |

Introduce a new grouping level when **3+ siblings** already share a real context. Do not invent a folder for a single speculative child.

## Safe-migration checklist

Copy and complete before finishing a restructure:

```
Migration:
- [ ] Inventory every inbound reference (skills, rules, AGENT.md, PLUGIN.md, indexes, docs)
- [ ] Move files and rewrite references in one change
- [ ] Update every index / manifest surface (skill maps, layout trees, glob rules)
- [ ] Verify nothing still resolves to the old path (search the repo)
- [ ] Leave no empty stub folder
- [ ] Prefer the cheapest move to undo (avoid drive-by renames of unrelated trees)
```

Do not leave permanent redirect stubs that duplicate content. A one-line pointer in an index or a deprecated note is enough when retrieval still needs the old name briefly.
