# Blueprint and data

## C++ owns systems; Blueprints compose

Gameplay-critical rules, replication, inventory, and scoring live in C++. Blueprints assemble actors, tune exposed properties, and implement presentation hooks. Do not copy a C++ state machine into a Blueprint graph "so designers can see it" — expose the hook instead.

## Exposure surface

| Macro | Meaning |
|---|---|
| `BlueprintNativeEvent` | C++ default; BP may override (`_Implementation` in C++) |
| `BlueprintImplementableEvent` | C++ fires; BP implements. No C++ body |
| `BlueprintCallable` | BP may call this C++ function |
| `Blueprintable` on `UCLASS` | Designers may subclass in BP |

Keep the callable surface small and typed. Prefer one function with a named struct over five `bool`/`float` parameters.

## Data

- Tune numbers and tags on `UDataAsset` / `UPrimaryDataAsset` subclasses, not magic constants in `BeginPlay`.
- `FGameplayTag` (or the project's tag type) for categorical ids — not raw `FString` compares.
- `FText` for anything displayed to a player. `FName` for stable keys. `FString` for transient / built strings only.

## Hard vs soft asset refs

A `UPROPERTY` `TObjectPtr<UTexture2D>` on a CDO is a hard reference: the texture cooks and loads with the class. Use `TSoftObjectPtr` + async load when the asset is optional or large. Do not `LoadSynchronous` on the game thread in `Tick` or `BeginPlay` of a frequently spawned actor.

## Do not

- Duplicate a C++ `switch` on an enum as a Blueprint chain that can drift.
- Put net-relevant state only in a Blueprint variable — it will not replicate unless C++ owns it.
- Call `CreateWidget` / load UI from an actor constructor.
