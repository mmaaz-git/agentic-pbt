# Bug Report: esp_idf_monitor.base.binlog Incorrect Octal Formatting for Zero

**Target**: `esp_idf_monitor.base.binlog.ArgFormatter`
**Severity**: Low
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The ArgFormatter incorrectly formats zero with the alternate octal form (`%#o`), producing "00" instead of the expected "0".

## Property-Based Test

```python
from hypothesis import given, strategies as st
from esp_idf_monitor.base.binlog import ArgFormatter

@given(st.integers(min_value=0, max_value=0o777777))
def test_octal_format(value):
    formatter = ArgFormatter()
    result_alt = formatter.c_format("%#o", [value])
    expected = f"0{value:o}" if value != 0 else "0"
    assert result_alt == expected
```

**Failing input**: `value=0`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/esp-idf-monitor_env/lib/python3.13/site-packages')
from esp_idf_monitor.base.binlog import ArgFormatter

formatter = ArgFormatter()
result = formatter.c_format("%#o", [0])
print(f"Result: '{result}'")
print(f"Expected: '0'")
assert result == "0", f"Expected '0' but got '{result}'"
```

## Why This Is A Bug

The C standard specifies that `%#o` with value 0 should produce "0", not "00". The alternate form (#) for octal should only add a leading zero for non-zero values. This violates the expected C printf behavior that the ArgFormatter is meant to emulate.

## Fix

```diff
--- a/esp_idf_monitor/base/binlog.py
+++ b/esp_idf_monitor/base/binlog.py
@@ -322,7 +322,7 @@ class ArgFormatter(string.Formatter):
     def format_field(self, value: Any, format_spec: str) -> Any:
         if 'o' in format_spec and '#' in format_spec:
             # Fix octal formatting (`0o377` → `0377`)
-            value = '0' + format(value, 'o')  # Correct prefix for C-style octal
+            value = '0' + format(value, 'o') if value != 0 else '0'  # Correct prefix for C-style octal
             format_spec = format_spec.replace('o', 's').replace('#', '')  # Remove '#' and replace 'o' with 's'
             format_spec = ('>' if '<' not in format_spec else '') + format_spec
         return super().format_field(value, format_spec)
```