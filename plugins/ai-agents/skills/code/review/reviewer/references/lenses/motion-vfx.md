# Lens — Motion / Animation / VFX UI

Activate for GSAP, Framer Motion, timelines, scrubbers, VFX galleries, curation carousels, showreel-like controls. Pair with `code/web/libs/react` (`gsap-patterns`), `code/web/ux`, and project `AGENT.md`.

## Hunt list

### Animation runtime
- Tweens/timelines killed on unmount; no orphaned `gsap` timers
- Animating React state every tick instead of refs / direct attrs
- Stacked timelines fighting the same property
- Reduced-motion: essential vs decorative motion gated correctly

### Interaction correctness
- Scrubber / slider / carousel keyboard support and focus
- Pointer + touch: drag conflicts with scroll/click
- TabIndex on non-interactive chrome; roving tabindex patterns wrong
- “Shown / seen / library” flags and persistence matching product rules in `AGENT.md`

### VFX / media UI
- Heavy media (video, Lottie, WebGL) mounted only when visible
- Prefetch/decode unbounded in lists
- Dispose/pause offscreen players
- Curation mutations (save, reorder, visibility) atomic and reversible on failure

### Continuity
- Fixing one control often breaks its twin (next/prev, thumbnail vs stage) — check siblings after any motion/VFX fix

Product intent for curation/VFX ownership lives in `AGENT.md` — do not invent “by design” without evidence; escalate product calls.
