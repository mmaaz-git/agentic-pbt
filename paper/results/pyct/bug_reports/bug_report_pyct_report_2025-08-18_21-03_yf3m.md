# Bug Report: pyct.report Output Format Ambiguity

**Target**: `pyct.report`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `report()` function in pyct.report produces ambiguous output when package names contain the delimiter sequence " # ", making it impossible to reliably parse the output format.

## Property-Based Test

```python
from hypothesis import given, strategies as st, assume, example
from pyct.report import report
import io
import sys

@given(st.text(min_size=1))
@example("package # comment")
def test_output_format_should_be_unambiguously_parseable(package_name):
    """The output format should be unambiguously parseable when split by ' # '"""
    assume('\x00' not in package_name)
    assume('\n' not in package_name)
    assume('\r' not in package_name)
    
    captured_output = io.StringIO()
    sys.stdout = captured_output
    try:
        report(package_name)
    finally:
        sys.stdout = sys.__stdout__
    
    output = captured_output.getvalue().strip()
    parts = output.split(' # ')
    
    assert len(parts) == 2, f"Output ambiguous! Got {len(parts)} parts: {parts}"
```

**Failing input**: `"package # comment"`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyct_env/lib/python3.13/site-packages')

from pyct.report import report

report("package # comment")
```

Output:
```
package # comment=unknown      # not installed in this environment
```

When parsed by splitting on " # ", this produces 3 parts instead of 2:
1. "package"
2. "comment=unknown     "
3. "not installed in this environment"

## Why This Is A Bug

The output format uses " # " as a delimiter between package info and location (line 57: `"{0:30} # {1}"`). When the package name itself contains " # ", the output becomes ambiguous and cannot be reliably parsed. Any tool consuming this output cannot distinguish between the delimiter and the literal " # " in the package name.

## Fix

```diff
--- a/pyct/report.py
+++ b/pyct/report.py
@@ -54,7 +54,10 @@ def report(*packages):
             else:
                 pass
         
-        print("{0:30} # {1}".format(package + "=" + ver,loc))
+        # Escape delimiter in package name to avoid ambiguity
+        safe_package = package.replace(" # ", " \\# ")
+        print("{0:30} # {1}".format(safe_package + "=" + ver, loc))
 
 
 def main():
```

Alternative fix: Use a different delimiter that's less likely to appear in package names, such as " :: " or " | ".