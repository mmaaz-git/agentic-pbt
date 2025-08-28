# Bug Report: dateutil.parser OverflowError on Large Numeric Strings

**Target**: `dateutil.parser.parse`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `dateutil.parser.parse()` function crashes with an unhandled OverflowError when parsing large numeric strings (15+ digits), instead of raising a proper ParserError or handling the value gracefully.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import dateutil.parser
import pytest

@given(st.text(alphabet="0123456789", min_size=15, max_size=20))
def test_large_numeric_strings_dont_crash(numeric_str):
    """Test that parser handles large numeric strings without crashing."""
    try:
        result = dateutil.parser.parse(numeric_str)
        # If it parses, should return a valid datetime
        assert isinstance(result, datetime)
    except dateutil.parser.ParserError:
        # Expected exception for unparseable strings
        pass
    except ValueError:
        # Also acceptable for invalid values
        pass
    # OverflowError should NOT occur - it should be caught and converted to ParserError
```

**Failing input**: `'000010000000000'`

## Reproducing the Bug

```python
import dateutil.parser

# This triggers an unhandled OverflowError
result = dateutil.parser.parse('000010000000000')
```

## Why This Is A Bug

The parser accepts the numeric string as potentially valid input and attempts to process it as a date/time value (possibly a timestamp or year). However, when it tries to create a datetime object with the large integer value, Python raises an OverflowError because the value exceeds what can be represented in a C int.

This is a bug because:
1. The parser should validate input values before attempting to create datetime objects
2. If an OverflowError occurs internally, it should be caught and converted to a ParserError
3. Users expect parser errors to be signaled via ParserError, not raw OverflowErrors

## Fix

The bug can be fixed by adding overflow checking in the `_build_naive` method of the parser:

```diff
--- a/dateutil/parser/_parser.py
+++ b/dateutil/parser/_parser.py
@@ -1232,7 +1232,12 @@ class parser(object):
             else:
                 repl[attr] = value
 
-        naive = default.replace(**repl)
+        try:
+            naive = default.replace(**repl)
+        except OverflowError as e:
+            raise ParserError(
+                "Date/time values out of range: {}".format(str(e))
+            ) from e
 
         if res.weekday is not None and not res.day:
             naive = naive + relativedelta.relativedelta(weekday=res.weekday)
```

This fix catches the OverflowError when datetime.replace() is called with out-of-range values and converts it to a proper ParserError that users expect from the parsing API.