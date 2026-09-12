# Content and VCS

## Feature folders, not type dumps

Assets live under `Content/<Feature>/...`, not loose in `Content/` and not in a repo-wide `Content/Materials` dump that mixes every system. The same feature's C++ lives under `Source/<Module>/`.

## Asset prefixes

| Prefix | Asset |
|---|---|
| `BP_` | Blueprint |
| `M_` | Material |
| `MI_` | Material instance |
| `T_` | Texture |
| `SK_` | Skeletal mesh |
| `SM_` | Static mesh |
| `A_` | Animation |
| `DA_` | Data asset |
| `WBP_` | Widget Blueprint |

Match the project's existing table when it differs; do not invent a third prefix for the same type.

## Git LFS

Track binary and UE serialized assets with LFS. A typical `.gitattributes` includes:

```
*.uasset filter=lfs diff=lfs merge=lfs -text
*.umap filter=lfs diff=lfs merge=lfs -text
*.png filter=lfs diff=lfs merge=lfs -text
*.fbx filter=lfs diff=lfs merge=lfs -text
*.wav filter=lfs diff=lfs merge=lfs -text
```

Use exclusive checkout / file locking for binary assets that cannot merge. Do not "resolve" a `.uasset` conflict by picking a side without opening the asset.

## Never commit

- `Binaries/`
- `Intermediate/`
- `Saved/`
- `DerivedDataCache/`
- local `*.user` editor files

These belong in `.gitignore`. They are machine-local and rebuild from source.

## Packaging notes

Document any custom cook / package steps in the project `AGENT.md`. Do not bury a required `-run=Cook` flag only in a teammate's memory.
