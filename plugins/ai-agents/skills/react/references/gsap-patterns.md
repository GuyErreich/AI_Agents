# GSAP & Animation-Library Integration

Patterns for using GSAP (and similar imperative animation libraries) inside React.

## Cleanup is mandatory

Any tween, timeline, or scroll trigger created in an effect must be reverted/killed in that effect's cleanup. Leaked tweens keep running and retain references after unmount.

```ts
useEffect(() => {
  const tween = gsap.to(el.current, { x: 100, duration: 1 });
  return () => {
    tween.kill();
  };
}, []);
```

## Dependency tracking with the React-aware hook

When using the framework hook (`useGSAP` or equivalent), pass a correct dependency list and scope so animations re-run only when intended and are cleaned up automatically. Do not rely on it to paper over missing dependencies.

## GPU acceleration

Enable GPU acceleration (`force3D: true`) for transform animations where supported, for smoother results.

## Do not drive continuous animation through React state

Prefer mutating the target element/ref directly via the animation library over `setState` in an update callback, which re-renders every frame.

## Typing

Type element refs to the concrete element type; type the library's objects with their exported types rather than `any`.
