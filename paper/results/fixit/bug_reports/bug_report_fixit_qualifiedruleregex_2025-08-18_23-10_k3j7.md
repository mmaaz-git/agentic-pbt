# Bug Report: fixit QualifiedRuleRegex Accepts Invalid Python Module Names

**Target**: `fixit.ftypes.QualifiedRuleRegex`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The QualifiedRuleRegex pattern incorrectly accepts module names that start with digits (e.g., "123module", "999rules"), which are invalid Python identifiers and cannot be imported.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from fixit.ftypes import QualifiedRuleRegex
import re

# Strategy for strings starting with a digit
invalid_module_strategy = st.from_regex(r"[0-9][a-zA-Z0-9_]*(\.[a-zA-Z0-9_]+)*", fullmatch=True)

@given(invalid_module_strategy)
def test_qualified_rule_regex_rejects_invalid_identifiers(invalid_module):
    """Test that QualifiedRuleRegex rejects module names starting with digits."""
    # Module names starting with digits should be rejected
    match = QualifiedRuleRegex.match(invalid_module)
    assert match is None, f"Should reject module starting with digit: {invalid_module}"
```

**Failing input**: `"123module"` (and many others like `"999rules"`, `"1.2.3"`)

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fixit_env/lib/python3.13/site-packages')

from fixit.ftypes import QualifiedRuleRegex
from fixit.config import parse_rule, find_rules
from pathlib import Path

# The regex incorrectly accepts module names starting with digits
match = QualifiedRuleRegex.match("123module")
print(f"QualifiedRuleRegex accepts '123module': {match is not None}")  # True (BUG!)

# This passes parsing but fails at import time
rule = parse_rule("123module", Path.cwd())
print(f"parse_rule succeeded: {rule}")  # Works

# But fails when trying to actually import
try:
    list(find_rules(rule))
except Exception as e:
    print(f"Import failed: {e}")  # CollectionError: could not import rule(s) 123module
```

## Why This Is A Bug

Python identifiers must start with a letter or underscore, not a digit. The regex pattern `[a-zA-Z0-9_]+` allows digits at the start, which violates Python's identifier rules. This causes the validation to pass at parse time but fail at import time, violating the fail-fast principle and producing confusing error messages.

## Fix

```diff
--- a/fixit/ftypes.py
+++ b/fixit/ftypes.py
@@ -85,11 +85,11 @@ LintIgnoreRegex = re.compile(
 QualifiedRuleRegex = re.compile(
     r"""
     ^
     (?P<module>
         (?P<local>\.)?
-        [a-zA-Z0-9_]+(\.[a-zA-Z0-9_]+)*
+        [a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)*
     )
     (?::(?P<name>[a-zA-Z0-9_]+))?
     $
     """,
     re.VERBOSE,
```