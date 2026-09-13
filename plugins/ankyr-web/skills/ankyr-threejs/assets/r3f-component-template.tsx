// React Three Fiber component scaffold.
//
// Requirements when adapting this template:
// 1. Functional TypeScript component — no `any`, no `@ts-nocheck`.
// 2. Import from `@react-three/fiber` and `@react-three/drei`.
// 3. If animated: declare vectors/colors/uniforms via `useMemo`/`useRef`
//    OUTSIDE the loop; never allocate inside `useFrame`.
// 4. Narrow `mesh.material` to the concrete material class before uniform access.
// 5. Named interfaces for all props — never `any[]`.
// 6. Dispose any geometry/material/texture created in component scope.
// 7. Confirm the result passes the project's lint and build commands.
//
// Place the component in the project's 3D components folder (see the nearest AGENT.md).

import { useFrame } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import type * as THREE from "three";

interface ExampleSceneProps {
  visible: boolean;
}

export const ExampleScene = ({ visible }: ExampleSceneProps) => {
  const meshRef = useRef<THREE.Mesh>(null);

  const uniforms = useMemo(
    () => ({
      uOpacity: { value: 0.0 },
    }),
    [],
  );

  useFrame(({ clock }) => {
    const mat = meshRef.current?.material as THREE.ShaderMaterial | undefined;
    if (mat) mat.uniforms.uOpacity.value = Math.min(1, clock.elapsedTime / 2);
  });

  if (!visible) return null;

  return (
    <mesh ref={meshRef}>
      <icosahedronGeometry args={[1, 4]} />
      <shaderMaterial uniforms={uniforms} transparent depthWrite={false} />
    </mesh>
  );
};
