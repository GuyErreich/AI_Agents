# Fixtures and fakes

## Shared fixtures

If two tests build the same object, extract a fixture. Compose fixtures (`event` uses `repo_dir`) instead of nesting setup in every test.

Put domain fixtures in one module (`tests/fixtures/` or the language equivalent). Do not grow a second copy in a nearby test file.

## When a fake beats a mock

| Prefer a fake / real file when… | Prefer a mock when… |
|---|---|
| The unit reads or writes files, YAML, or JSON | The collaborator is a remote API or git process |
| You are asserting the written bytes | You only need to confirm a call happened |
| The real type is small and deterministic | Constructing the real type needs the network |

A fake is an in-process stand-in with the same interface (in-memory repo, temp clock). A mock records calls and returns scripted values. Fakes catch more contract drift.

## Do not mock internals

Mocking `module._helper` to force a path couples the test to a private name. Drive that path through the public API, or extract a seam you own and fake *that*.

Repeated `mocker.patch(...)` blocks across tests belong in a fixture that yields the configured fake.
