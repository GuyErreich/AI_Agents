# Lifecycle and Tick

## Constructor = CDO defaults only

The constructor runs for the Class Default Object in any process that loads the class (editor, cook, dedicated server). It must not:

- Touch `GetWorld()`, spawn actors, load assets synchronously, or play gameplay
- Bind delegates that assume a live world
- Allocate per-instance runtime caches that belong in `BeginPlay`

Set default property values and create default subobjects (`CreateDefaultSubobject`) here. That's it.

## Construction vs play

| Callback | When | Use for |
|---|---|---|
| `OnConstruction` | CDO + placed instances, including construction script | Editor-time mesh/setup from properties |
| `PostInitializeComponents` | Components exist, world may be valid | Wire component refs |
| `BeginPlay` | Game has started for this actor | Bind, spawn runtime helpers, start timers |
| `EndPlay` | Actor leaving play | Unbind delegates, clear timers, release runtime objects |

Do not assume two actors' `BeginPlay` order. Find or spawn collaborators explicitly; do not rely on level-load sequence.

## Tick discipline

```cpp
AMyActor::AMyActor()
{
  PrimaryActorTick.bCanEverTick = false;
}
```

Enable Tick only when the actor must run every frame (and document why). Prefer:

- `FTimerHandle` / `GetWorldTimerManager()` for delayed or periodic work
- Delegates (`OnTakeAnyDamage`, custom) for event-driven work
- World / game-instance subsystems for shared ticking

Inside Tick (when it is justified): no `NewObject`, no string formatting, no `TArray` realloc of a hot buffer. Reuse members allocated at `BeginPlay`.

## Cleanup

Clear timers and unbind delegates in `EndPlay` (and on the matching `EndPlay` reason). A bound lambda that captures `this` after `EndPlay` is a use-after-destroy.

`Destroy()` is a request. Do not use the actor after calling it; finish the frame and let GC / destruction proceed.
