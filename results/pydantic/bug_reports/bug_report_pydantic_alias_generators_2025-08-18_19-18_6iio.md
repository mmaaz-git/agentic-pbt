# Bug Report: pydantic.alias_generators Breaks Round-Trip and Idempotence Properties

**Target**: `pydantic.alias_generators`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The case conversion functions in `pydantic.alias_generators` violate round-trip and idempotence properties due to inconsistent handling of letter-digit boundaries.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from pydantic.alias_generators import to_camel, to_snake

@given(st.from_regex(r'^[a-z][a-z0-9]*$', fullmatch=True))
def test_round_trip_snake_to_camel_to_snake(s):
    """Converting to camelCase and back should preserve the original"""
    result = to_snake(to_camel(s))
    assert result == s, f"Round trip failed for '{s}': got '{result}'"
```

**Failing input**: `'a0'`

## Reproducing the Bug

```python
from pydantic.alias_generators import to_camel, to_pascal, to_snake

# Bug 1: to_snake is not idempotent
input1 = 'A0'
once = to_snake(input1)  # Returns 'a0'
twice = to_snake(once)   # Returns 'a_0'
assert once == twice  # Fails: 'a0' != 'a_0'

# Bug 2: Round-trip through camel fails
input2 = 'value1'
result = to_snake(to_camel(input2))  # Returns 'value_1' instead of 'value1'
assert result == input2  # Fails

# Bug 3: Round-trip through pascal fails  
input3 = 'a_0'
result = to_snake(to_pascal(input3))  # Returns 'a0' instead of 'a_0'
assert result == input3  # Fails
```

## Why This Is A Bug

The functions claim to convert between naming conventions, but they violate fundamental properties:

1. **Idempotence violation**: `to_snake` applied twice produces different results
2. **Round-trip violation**: Converting to another format and back doesn't preserve the original
3. **Common identifiers affected**: Identifiers like `value1`, `api2`, `sha256` all fail round-trips

The root cause is that `to_snake` inserts underscores between letters and digits (`a0` -> `a_0`), but `to_pascal` removes all underscores (`a_0` -> `A0`), creating an asymmetry.

## Fix

The issue is in the `to_snake` function which has a regex that inserts underscores between lowercase letters and digits. This should be reconsidered to maintain consistency:

```diff
def to_snake(camel: str) -> str:
    """Convert a PascalCase, camelCase, or kebab-case string to snake_case."""
    snake = re.sub(r'([A-Z]+)([A-Z][a-z])', lambda m: f'{m.group(1)}_{m.group(2)}', camel)
    snake = re.sub(r'([a-z])([A-Z])', lambda m: f'{m.group(1)}_{m.group(2)}', snake)
    snake = re.sub(r'([0-9])([A-Z])', lambda m: f'{m.group(1)}_{m.group(2)}', snake)
-   snake = re.sub(r'([a-z])([0-9])', lambda m: f'{m.group(1)}_{m.group(2)}', snake)
+   # Don't insert underscore between letter and digit for consistency
    snake = snake.replace('-', '_')
    return snake.lower()
```

Alternatively, maintain the current behavior but update `to_pascal` to preserve the semantic boundary information when converting `a_0` style patterns.