# Three.js Resource Disposal

Geometries, materials, and textures hold GPU memory. Dispose everything created in component scope.

```tsx
useEffect(() => {
  const geom = new THREE.IcosahedronGeometry(10, 4);
  const mat = new THREE.MeshPhongMaterial({ color: 0xff0000 });
  const mesh = new THREE.Mesh(geom, mat);
  groupRef.current?.add(mesh);

  return () => {
    geom.dispose();
    mat.dispose();
    if (mesh.parent) mesh.parent.remove(mesh);
  };
}, []);
```

## Textures

```tsx
const texture = useMemo(() => new THREE.TextureLoader().load("/image.webp"), []);
useEffect(() => () => texture.dispose(), [texture]);
```

## Reuse over recreate

Create geometries/materials once via `useMemo` and reuse across frames and instances. Do not create them inside `useFrame`.

## Checklist

- [ ] Every geometry created in scope is disposed in cleanup.
- [ ] Every material created in scope is disposed in cleanup.
- [ ] Every texture created in scope is disposed in cleanup.
- [ ] Meshes are removed from their parent on unmount.
