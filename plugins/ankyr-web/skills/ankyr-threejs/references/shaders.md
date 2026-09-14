# Shaders & Material Typing

## Stable uniforms via useMemo

Define uniforms once so the object reference is stable across renders:

```ts
const uniforms = useMemo(
  () => ({
    uOpacity: { value: 0.0 },
    uIntensity: { value: 1.0 },
    uSize: { value: 3.0 },
  }),
  [],
);
```

Mutate `.value` inside the loop, never replace the object:

```ts
useFrame(({ clock }) => {
  const mat = meshRef.current.material as THREE.ShaderMaterial;
  mat.uniforms.uOpacity.value = Math.min(1, clock.elapsedTime / 2);
});
```

Attach to the material in JSX:

```tsx
<shaderMaterial
  uniforms={uniforms}
  vertexShader={vertexShader}
  fragmentShader={fragmentShader}
  transparent
  blending={THREE.AdditiveBlending}
  depthWrite={false}
/>
```

## Material typing

Narrow to the concrete material class before accessing members specific to it:

```ts
// BAD — uniforms does not exist on the base type
meshRef.current.material.uniforms.uOpacity.value = 1;

// GOOD
const mat = meshRef.current.material as THREE.ShaderMaterial;
mat.uniforms.uOpacity.value = 1;
```

## Typed shared loop helpers

Type every parameter of helpers called from `useFrame`; never leave implicit `any`.

## BufferGeometry attributes

Cast the attribute `array` to the concrete typed array after reading it from R3F's `attributes`.
