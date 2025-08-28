# Bug Report: pydantic.experimental.pipeline str_strip Does Not Strip All Unicode Whitespace

**Target**: `pydantic.experimental.pipeline._Pipeline.str_strip`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `str_strip()` method in pydantic.experimental.pipeline does not strip all Unicode whitespace characters that Python's built-in `str.strip()` removes, leading to inconsistent behavior.

## Property-Based Test

```python
from typing import Annotated
from hypothesis import given, strategies as st
from pydantic import BaseModel
from pydantic.experimental.pipeline import validate_as

@given(st.text(alphabet=st.characters(whitelist_categories=('Zs', 'Cc'))))
def test_str_strip_matches_python(s: str):
    """Test that pipeline str_strip matches Python's str.strip behavior"""
    
    class StripModel(BaseModel):
        value: Annotated[str, validate_as(str).str_strip()]
    
    result = StripModel(value=s).value
    expected = s.strip()
    
    assert result == expected, f"Pydantic stripped to {result!r}, Python to {expected!r}"
```

**Failing input**: `'\x1f'` (Unit Separator character, Unicode U+001F)

## Reproducing the Bug

```python
from typing import Annotated
from pydantic import BaseModel
from pydantic.experimental.pipeline import validate_as

test_char = '\x1f'  # Unit Separator - a whitespace character

class StripModel(BaseModel):
    value: Annotated[str, validate_as(str).str_strip()]

result = StripModel(value=test_char)

print(f"Input: {test_char!r}")
print(f"Python strip(): {test_char.strip()!r}")  # Returns ''
print(f"Pydantic str_strip(): {result.value!r}")  # Returns '\x1f'

assert result.value == test_char.strip(), "str_strip doesn't match Python's behavior"
```

## Why This Is A Bug

The `str_strip()` method in the pipeline API is expected to behave like Python's `str.strip()` method, as evidenced by:
1. The method name directly references the Python string method
2. The implementation delegates to pydantic_core's `strip_whitespace` flag (line 429-430 in pipeline.py)
3. The docstring states it performs a "strip" transformation (line 311)

However, it fails to strip several Unicode whitespace characters that Python considers whitespace, including:
- `\x1c` to `\x1f` (Information Separator characters)
- `\x0b` (Vertical Tab)
- `\x0c` (Form Feed)
- `\x85` (Next Line)
- `\xa0` (Non-breaking Space)

This violates the reasonable expectation that a method named `str_strip()` would behave consistently with Python's built-in `str.strip()`.

## Fix

The issue appears to be in pydantic_core's implementation of `strip_whitespace`, which likely uses a more restrictive definition of whitespace than Python's `str.strip()`. The fix would require updating the core schema's string validator to use Python's full Unicode whitespace definition when `strip_whitespace=True`.

```diff
# In pydantic_core's string validation (conceptual fix)
- # Current: Only strips common ASCII whitespace like space, tab, newline
+ # Fixed: Use Python's str.strip() or match its Unicode whitespace definition
+ # to include all characters where char.isspace() returns True
```