# Bug Report: google.api_core.protobuf_helpers.check_oneof Error Message Formatting Issue

**Target**: `google.api_core.protobuf_helpers.check_oneof`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `check_oneof` function produces malformed error messages when dictionary keys contain special characters like newlines, resulting in confusing error messages that break across multiple lines.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pytest
from google.api_core import protobuf_helpers

@given(st.dictionaries(
    st.text(min_size=1, max_size=10),
    st.one_of(st.none(), st.integers(), st.text()),
    min_size=0,
    max_size=5
))
def test_protobuf_check_oneof(kwargs):
    """Test check_oneof raises ValueError for multiple non-None values."""
    non_none_count = sum(1 for v in kwargs.values() if v is not None)
    
    if non_none_count > 1:
        # Should raise ValueError with properly formatted message
        with pytest.raises(ValueError, match="Only one of .* should be set"):
            protobuf_helpers.check_oneof(**kwargs)
    else:
        # Should not raise
        protobuf_helpers.check_oneof(**kwargs)
```

**Failing input**: `kwargs={'0': 0, '\n': 0}`

## Reproducing the Bug

```python
from google.api_core import protobuf_helpers

# Keys with special characters break error message formatting
protobuf_helpers.check_oneof(**{'0': 0, '\n': 0})
```

Output:
```
ValueError: Only one of 
, 0 should be set.
```

## Why This Is A Bug

The error message includes the literal newline character in the output, creating a confusing multi-line error message. The function should properly escape or handle special characters in key names when constructing the error message. The current output "Only one of \n, 0 should be set." is difficult to understand and debug.

## Fix

```diff
--- a/google/api_core/protobuf_helpers.py
+++ b/google/api_core/protobuf_helpers.py
@@ -87,8 +87,8 @@ def check_oneof(**kwargs):
     if len(not_nones) > 1:
         raise ValueError(
             "Only one of {fields} should be set.".format(
-                fields=", ".join(sorted(kwargs.keys()))
+                fields=", ".join(repr(k) for k in sorted(kwargs.keys()))
             )
         )
```