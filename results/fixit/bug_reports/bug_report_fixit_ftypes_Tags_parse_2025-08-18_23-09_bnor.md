# Bug Report: fixit.ftypes.Tags.parse IndexError on Whitespace Input

**Target**: `fixit.ftypes.Tags.parse`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `Tags.parse()` static method crashes with an IndexError when given input strings that contain only whitespace or result in empty tokens after splitting and stripping.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from fixit.ftypes import Tags

@given(st.text())
def test_tags_parse_empty_or_none(tag_string):
    """Empty or whitespace-only strings should produce empty Tags"""
    if tag_string.strip() == "":
        tags = Tags.parse(tag_string)
        assert tags.include == ()
        assert tags.exclude == ()
        assert not tags  # __bool__ should return False
```

**Failing input**: `' '` (single space character)

## Reproducing the Bug

```python
from fixit.ftypes import Tags

# All of these cause IndexError
Tags.parse(" ")       # Single space
Tags.parse("  \t  ")  # Multiple whitespace characters
Tags.parse(" , ")     # Comma with only whitespace
```

## Why This Is A Bug

The function should gracefully handle whitespace-only input strings. The current implementation assumes that after splitting and stripping, all tokens will have at least one character, but this assumption is violated when the input contains only whitespace or empty comma-separated values. This would affect any user or system that passes user input directly to this parsing function without pre-validation.

## Fix

```diff
@staticmethod
def parse(value: Optional[str]) -> "Tags":
    if not value:
        return Tags()

    include = set()
    exclude = set()
    tokens = {value.strip() for value in value.lower().split(",")}
    for token in tokens:
+       if not token:  # Skip empty tokens
+           continue
        if token[0] in "!^-":
            exclude.add(token[1:])
        else:
            include.add(token)

    return Tags(
        include=tuple(sorted(include)),
        exclude=tuple(sorted(exclude)),
    )
```