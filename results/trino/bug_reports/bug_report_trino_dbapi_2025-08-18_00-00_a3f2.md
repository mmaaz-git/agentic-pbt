# Bug Report: trino.dbapi Large Integer Overflow

**Target**: `trino.dbapi._format_prepared_param`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `_format_prepared_param` method in trino.dbapi fails to convert integers exceeding the 64-bit BIGINT range to DECIMAL format, despite a TODO comment indicating this should be done. This causes potential overflow errors when large Python integers are sent to the database.

## Property-Based Test

```python
from hypothesis import given, strategies as st, settings
from trino.dbapi import Cursor, Connection
from unittest.mock import Mock

BIGINT_MAX = 2**63 - 1
BIGINT_MIN = -(2**63)

@given(
    value=st.integers(min_value=BIGINT_MAX + 1, max_value=2**100)
)
@settings(max_examples=50)
def test_integers_above_bigint_max(value):
    """Test that integers above BIGINT max should be formatted as DECIMAL"""
    mock_connection = Mock(spec=Connection)
    cursor = Cursor(mock_connection, Mock(), legacy_primitive_types=False)
    
    result = cursor._format_prepared_param(value)
    
    # These should be DECIMAL according to TODO comment
    assert result.startswith("DECIMAL"), \
        f"Integer {value} exceeding BIGINT max should be DECIMAL. Got: {result}"
```

**Failing input**: `9223372036854775808` (2^63, which is BIGINT_MAX + 1)

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/trino_env/lib/python3.13/site-packages')

from trino.dbapi import Cursor, Connection
from unittest.mock import Mock

mock_connection = Mock(spec=Connection)
cursor = Cursor(mock_connection, Mock(), legacy_primitive_types=False)

# BIGINT_MAX is 2^63 - 1
BIGINT_MAX = 9223372036854775807
large_int = BIGINT_MAX + 1  # 2^63

result = cursor._format_prepared_param(large_int)
print(f"Input: {large_int}")
print(f"Output: {result}")
print(f"Expected: DECIMAL '{large_int}'")

assert result == str(large_int)  # Currently returns plain integer
assert not result.startswith("DECIMAL")  # Should be DECIMAL but isn't
```

## Why This Is A Bug

The code contains a TODO comment at line 530 explicitly stating "represent numbers exceeding 64-bit (BIGINT) as DECIMAL", but this is not implemented. Python supports arbitrary precision integers, but SQL BIGINT is limited to 64 bits. Sending integers outside this range as plain integers will cause:
1. Database overflow errors
2. Silent truncation or wraparound
3. Data corruption

The bug violates the documented intent of the code and can cause runtime failures when Python's unlimited integers exceed SQL's BIGINT range.

## Fix

```diff
--- a/trino/dbapi.py
+++ b/trino/dbapi.py
@@ -527,8 +527,10 @@ class Cursor:
             return "true" if param else "false"
 
         if isinstance(param, int):
-            # TODO represent numbers exceeding 64-bit (BIGINT) as DECIMAL
+            # Represent numbers exceeding 64-bit (BIGINT) as DECIMAL
+            if param < -(2**63) or param > (2**63 - 1):
+                return "DECIMAL '%d'" % param
             return "%d" % param
 
         if isinstance(param, float):
```