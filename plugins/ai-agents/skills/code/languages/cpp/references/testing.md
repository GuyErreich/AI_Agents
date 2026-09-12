# C++ — GoogleTest / Catch2

This file is the C++ test *how*. Use the runner the repo already chose; do not add a second framework.

- Prefer **GoogleTest** or **Catch2** — not a home-grown `main` with raw asserts.
- Shared setup lives in fixtures or a `tests/fixtures/` (or the path the repo already uses). Do not paste setup into each file.
- Prefer real files or an in-memory fake at the I/O boundary over mocking every collaborator. Mock subprocess / network / time at the boundary; do not mock the function under test.
- Parameterize edge cases (empty, max, invalid UTF-8, missing file) rather than copying test bodies.
- Type-annotate test helpers. A one-line comment on a non-obvious fixture is enough — do not write essay docstrings.

```cpp
TEST(ParseVersion, Quoted) {
  const auto parsed = parse_version(R"("1.2.3")");
  ASSERT_TRUE(parsed.has_value());
  EXPECT_EQ(*parsed, Version{1, 2, 3});
}
```

## Sanitizers

Run the test binary under ASan/UBSan (and TSan in its own preset) as configured in `references/tooling.md`. A leak, use-after-free, or data race is a failed test.

## Naming and layout

- Test file names follow the project convention (`*_test.cpp` or `test_*.cpp`). Mirror the source path when the tree already does.
- One fixture per collaborator set. Tear down in the fixture destructor (RAII), not a manual `TearDown` that can be skipped.

All generated tests must pass the repo Validate suite (build, tidy/format when listed, tests).
