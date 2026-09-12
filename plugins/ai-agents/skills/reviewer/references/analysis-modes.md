# Analysis modes (prompt-level)

Optional stance for the reviewer skill and `pr-reviewer` loop agent. Controlled by durable preference / orchestrator input `analysis_mode`.

**Non-goal:** this does **not** change Cursor's chat mode dropdown (Agent / Plan / Debug / Multitask / Ask). Subagents cannot be launched into those UI modes. `analysis_mode` only reshapes investigation instructions and finding quality bars.

## Values

| Mode | When | Finding quality bar |
|---|---|---|
| `review` (default) | Normal staff-bar review | Current behavior: concrete failure mode, severity, location |
| `debug-like` | Deeper semantic / causality passes | Each finding: **observed** → **expected contract** → **causal why** (or mark speculative). Prefer fewer high-confidence issues over cosmetic nits |
| `security` | Auth / data / secrets heavy diffs | Same as `review`, plus threat-pass emphasis; auth/data rows must include an **abuse path** |

Aliases (normalized in `_loop_state.normalize_analysis_mode`):

- `debug` → `debug-like`
- `sec` / `secure` → `security`
- `default` / `standard` → `review`

## Scope discipline

`debug-like` and `security` raise the **evidence** bar. They do **not** expand coverage denominator **M** beyond the round focus or post-fix verify surface (see `thoroughness-pass.md`). Expanding M under `debug-like` causes rediscovery thrash and fights loop convergence.

## Loop usage

- Orchestrator passes `analysis_mode` from `state.json` on every `pr-reviewer` launch.
- Invocation: `analysis debug`, `analysis_mode=security`, `debug-like review`.
- Pairing tip: `analysis debug` + `reviewer_model=opus` for hardest analysis without claiming Debug UI mode.

## Manual reviews

When the user asks for a self-review or PR review outside the loop and names a mode, load this file and apply the matching bar. Default remains `review`.
