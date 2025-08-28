# Bug Report: packaging.tags Case Normalization Failure for Special Unicode Characters

**Target**: `packaging.tags.Tag`
**Severity**: Low
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The Tag class fails to maintain case-insensitive equality for Unicode characters with special case mappings like German eszett (ß → SS).

## Property-Based Test

```python
@given(
    interpreter=st.text(min_size=1, max_size=20).filter(lambda s: not any(c in s for c in ".-")),
    abi=st.text(min_size=1, max_size=20).filter(lambda s: not any(c in s for c in ".-")),
    platform=st.text(min_size=1, max_size=20).filter(lambda s: not any(c in s for c in ".-"))
)
def test_tag_case_normalization(interpreter, abi, platform):
    """Test that tags normalize to lowercase."""
    tag_lower = packaging.tags.Tag(interpreter.lower(), abi.lower(), platform.lower())
    tag_upper = packaging.tags.Tag(interpreter.upper(), abi.upper(), platform.upper())
    tag_mixed = packaging.tags.Tag(interpreter, abi, platform)
    
    assert tag_lower == tag_upper
    assert tag_lower == tag_mixed
    assert tag_upper == tag_mixed
```

**Failing input**: `interpreter='0', abi='0', platform='ß'`

## Reproducing the Bug

```python
import packaging.tags

tag_with_eszett = packaging.tags.Tag('py3', 'none', 'ß')
tag_with_upper = packaging.tags.Tag('py3', 'none', 'ß'.upper())  # 'SS'

print(f"Tag with ß: {tag_with_eszett}")
print(f"Tag with SS: {tag_with_upper}")
print(f"Are they equal? {tag_with_eszett == tag_with_upper}")

assert tag_with_eszett == tag_with_upper
```

## Why This Is A Bug

The Tag class documentation states that instances normalize to lowercase and support equality checking. However, for characters like German eszett (ß), the normalization is inconsistent:
- `ß.upper()` becomes `SS`
- `SS.lower()` becomes `ss`
- But `ß.lower()` remains `ß`

This breaks the expected property that `Tag(x.lower()) == Tag(x.upper())` for all strings x.

## Fix

```diff
class Tag:
    def __init__(self, interpreter: str, abi: str, platform: str) -> None:
-       self._interpreter = interpreter.lower()
-       self._abi = abi.lower()
-       self._platform = platform.lower()
+       # Use casefold() for proper Unicode case-insensitive comparison
+       self._interpreter = interpreter.casefold()
+       self._abi = abi.casefold()
+       self._platform = platform.casefold()
        self._hash = hash((self._interpreter, self._abi, self._platform))
```