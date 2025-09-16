# Bug Report: Cython.TestUtils strip_common_indent Fails to Handle Tab Indentation

**Target**: `Cython.TestUtils.strip_common_indent`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `strip_common_indent` function claims to strip "common indentation" but only handles spaces, completely ignoring tab characters, which are a valid and common form of indentation.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import Cython.TestUtils

@given(
    common_indent=st.text(alphabet=' \t', min_size=1, max_size=10),
    suffixes=st.lists(st.text(min_size=1), min_size=1, max_size=10)
)
def test_strip_common_indent_removes_common_prefix(common_indent, suffixes):
    """Common indentation should be completely removed"""
    lines = [common_indent + suffix for suffix in suffixes]
    result = Cython.TestUtils.strip_common_indent(lines)
    
    for i, line in enumerate(result):
        assert not line.startswith(common_indent) or suffixes[i].startswith(common_indent), \
            f"Common indent not fully removed: {repr(line)}"
```

**Failing input**: `common_indent='\t'`, `suffixes=['0']`

## Reproducing the Bug

```python
import Cython.TestUtils

# Test with tab indentation
lines_with_tabs = ['\ta', '\tb', '\tc']
result = Cython.TestUtils.strip_common_indent(lines_with_tabs)
print(f"Input: {lines_with_tabs}")
print(f"Output: {result}")
print(f"Expected: ['a', 'b', 'c']")

# Compare with space indentation (which works)
lines_with_spaces = ['    a', '    b', '    c']
result = Cython.TestUtils.strip_common_indent(lines_with_spaces)
print(f"\nSpaces work correctly: {result}")
```

## Why This Is A Bug

The function's docstring states it "Strips empty lines and common indentation from the list of strings given in lines". Tab characters (`\t`) are a standard form of indentation in programming, used by many text editors and coding standards. The function correctly handles space-based indentation but completely fails to recognize tabs as indentation, violating the expected behavior described in its documentation.

## Fix

The issue appears to be that the internal `_match_indent` pattern only matches spaces (`^[ ]*`) instead of all whitespace. The fix would be to update the regex pattern to match both spaces and tabs:

```diff
- _match_indent = re.compile(r'^[ ]*')
+ _match_indent = re.compile(r'^[ \t]*')
```

This would allow the function to correctly handle both space and tab indentation, as well as mixed indentation scenarios.