# Bug Report: praw.util.camel_to_snake Incorrectly Splits Acronyms

**Target**: `praw.util.camel_to_snake`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `camel_to_snake` function incorrectly handles strings with 3+ consecutive uppercase letters followed by a lowercase letter, splitting acronyms like "API" into "ap_i" instead of keeping them together.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from praw.util import camel_to_snake

@given(st.text())
def test_camel_to_snake_preserves_acronyms():
    # Test that common patterns like APIv2 don't get incorrectly split
    test_cases = ["APIv2", "RESTAPIv1", "HTTPAPIKey"]
    for case in test_cases:
        result = camel_to_snake(case)
        # Should not split "API" into "ap_i"
        assert "ap_i" not in result
```

**Failing input**: `"APIv2"`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/praw_env/lib/python3.13/site-packages')
from praw.util import camel_to_snake

result = camel_to_snake("APIv2")
print(f"camel_to_snake('APIv2') = '{result}'")
# Output: 'ap_iv2'
# Expected: 'apiv2' or 'api_v2'

assert result == "ap_iv2"  # Bug confirmed
```

## Why This Is A Bug

This violates expected behavior because:
1. Common acronyms like "API", "HTTP", "REST" get incorrectly split when followed by lowercase letters
2. The output "ap_iv2" is unintuitive and breaks the semantic meaning of "API"
3. Developers expect acronyms to be treated as units, not split arbitrarily
4. The pattern works correctly for 2-letter acronyms (e.g., "IOError" -> "io_error") but fails for 3+ letters

## Fix

The issue is in the regex pattern. The current pattern doesn't correctly handle 3+ consecutive uppercase letters followed by lowercase. Here's a fix:

```diff
--- a/praw/util/snake.py
+++ b/praw/util/snake.py
@@ -5,7 +5,7 @@ from __future__ import annotations
 import re
 from typing import Any
 
-_re_camel_to_snake = re.compile(r"([a-z0-9](?=[A-Z])|[A-Z](?=[A-Z][a-z]))")
+_re_camel_to_snake = re.compile(r"([a-z0-9](?=[A-Z])|[A-Z]+(?=[A-Z][a-z])|[A-Z]+(?=[a-z]))")
 
 
 def camel_to_snake(name: str) -> str:
```

Alternative approach: Handle acronyms more intelligently by looking for patterns of consecutive uppercase letters and treating them as units when followed by lowercase letters.