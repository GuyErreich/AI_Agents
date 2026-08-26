# Lens — Realtime Graphics (Three / R3F / WebGL)

Activate with `code/web/libs/threejs` and `code/quality/performance` when R3F/Three/shaders/GPU paths change.

## Hunt list

### Frame budget
- Allocations inside `useFrame` / render loop (`new` Vector/Color/Matrix/Geometry/Material)
- `setState` per frame driving animation
- Unstable uniform object identity (rebuilt each render)

### Resource lifetime
- Geometries, materials, textures, render targets disposed on unmount
- Trailing GPU resources when hot-reloading or switching scenes
- Event listeners / `useFrame` subscriptions cleaned up

### Correctness
- Refs typed to concrete Three classes; materials narrowed before `.uniforms`
- Lights/cameras/scales sane; matrices updated when parents move
- Instancing vs per-mesh explosion for repeated geometry

### Integration
- R3F vs raw Three antipatterns (prefer drei/`useFrame` per skill)
- Canvas / DPR / resize handlers not leaking or thrashing

Performance findings need a plausible jank or leak path — not micro-advice.
