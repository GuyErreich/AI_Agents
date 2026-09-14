# Specialist Lenses — Router

One reviewer, many specialist minds. **Do not** spawn nested Task/subagents for lenses — unsupported in the PR loop and hangs the parent. Activate every matching lens in the same pass after Phase 0.

## How to activate

1. From the tier diff path list, mark each matching row below.
2. Load that lens file and hunt its checklist on the matching files.
3. Still load the domain **skills** in the main routing table (lenses are review hunting packs; skills are the full standards).
4. Report activated lenses in coverage: `lenses: frontend+motion-vfx`.

| Lens | Activate when diff touches | File |
|---|---|---|
| **staff-bar** | Always (every review) | `lenses/staff-bar.md` |
| **typescript** | `*.{ts,tsx,js,mjs,cjs}` | `lenses/typescript.md` |
| **frontend** | Components, pages, hooks, CSS, UI kits, a11y-sensitive UI | `lenses/frontend.md` |
| **backend** | Supabase, SQL/migrations, edge functions, RLS, auth, API routes, env/secrets | `lenses/backend.md` |
| **realtime-graphics** | `three` / R3F / WebGL / shaders / GPU buffers / canvases | `lenses/realtime-graphics.md` |
| **motion-vfx** | GSAP, Framer Motion, timeline/tween, VFX/curation sliders, scrubbers, showreel-like UI | `lenses/motion-vfx.md` |

If unsure, activate the stricter lens. Missing a lens is worse than an extra one.
