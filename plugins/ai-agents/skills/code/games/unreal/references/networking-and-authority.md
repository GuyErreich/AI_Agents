# Networking and authority

## Server owns the truth

Mutate gameplay state on the authority. Clients predict presentation only. `HasAuthority()` (or `GetLocalRole() == ROLE_Authority`) before applying damage, inventory, scoring, or game-mode transitions.

```cpp
void AMyActor::ApplyHit(float Damage)
{
  if (!HasAuthority()) {
    return;
  }
  Health = FMath::Max(0.f, Health - Damage);
}
```

## Replication

- Every replicated field is listed in `GetLifetimeReplicatedProps` with `DOREPLIFETIME` / `DOREPLIFETIME_CONDITION`.
- `ReplicatedUsing=OnRep_Foo` for client-side reaction (VFX, UI). The `OnRep` must tolerate being called with the same value and on initial bunches.
- Do not replicate a value the client can derive (unless you measured that derivation is worse than the bandwidth).

## RPCs

| Type | Runs on | Use |
|---|---|---|
| `Server` | Authority | Client request ("I pressed fire") |
| `Client` | Owning client | Server → one client (UI, camera) |
| `NetMulticast` | All connections | Cosmetic events; not gameplay truth |

Server RPCs that change state have a `_Validate` that rejects impossible values (NaN, negative ammo, out-of-range enum). Never trust the client payload — treat it as input, not a command. Ties to `code/quality/security`.

```cpp
UFUNCTION(Server, Reliable, WithValidation)
void ServerFire(FVector_NetQuantize Aim);

bool AMyCharacter::ServerFire_Validate(FVector_NetQuantize Aim)
{
  return Aim.ContainsNaN() == false;
}
```

## Ownership and relevancy

- `bOnlyRelevantToOwner` for private UI/state. Do not net-multicast secrets.
- RPCs on an actor the caller does not own will not run. Check ownership before designing the call path.

## Do not

- Run gameplay-critical logic only in a `NetMulticast` — a late joiner or a packet drop desyncs.
- Read `GetPing` / client clocks as authority for hit registration.
- Expose a `BlueprintCallable` Server RPC without validation because "designers will be careful."
