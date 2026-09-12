# R3F Render-Loop Lifecycle

## Never allocate inside `useFrame`

Allocating an object every frame causes GC stutter within seconds.

```ts
// BAD — new Vector3 60x/second
useFrame(() => {
  mesh.current.position.add(new THREE.Vector3(0, 0.01, 0));
});

// GOOD — allocate once, reuse
const vel = useMemo(() => new THREE.Vector3(0, 0.01, 0), []);
useFrame(() => {
  mesh.current.position.add(vel);
});
```

## Mutate, do not re-render, per frame

```ts
// BAD — re-renders every frame
const [opacity, setOpacity] = useState(0);
useFrame(() => setOpacity(t));

// GOOD — mutate the uniform directly
const mat = meshRef.current.material as THREE.ShaderMaterial;
mat.uniforms.uOpacity.value = t;
```

## Use the ecosystem

Prefer `@react-three/drei` helpers (`<Float>`, `useGLTF`, `<Sparkles>`, `<Stats>`, `<OrbitControls>`) over hand-rolled equivalents. Drive animation with `useFrame` — never raw `requestAnimationFrame` inside a component.

## Typed refs

```ts
const meshRef = useRef<THREE.Mesh>(null);
const groupRef = useRef<THREE.Group>(null);
const pointsRef = useRef<THREE.Points>(null);
```

## Instancing

Use `THREE.InstancedMesh` for many identical geometries (stars, dust, particles). Update per-instance transforms with a reusable dummy object and `setMatrixAt`, then set `instanceMatrix.needsUpdate = true`.
