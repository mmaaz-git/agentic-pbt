# Bug Report: fixit.ftypes LintIgnoreRegex Silently Ignores All Rules on Malformed Input

**Target**: `fixit.ftypes.LintIgnoreRegex`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The LintIgnoreRegex fails to properly handle rule names that start with non-word characters, causing malformed lint directives to silently ignore ALL rules instead of none.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import fixit.ftypes as ftypes

@given(st.sampled_from(["lint-ignore", "lint-fixme"]),
       st.one_of(st.none(), st.lists(st.text(min_size=1), min_size=1, max_size=5)))
def test_lint_ignore_regex(directive, rule_names):
    if rule_names is None:
        comment = f"# {directive}"
    else:
        names_str = ", ".join(rule_names)
        comment = f"# {directive}: {names_str}"
    
    match = ftypes.LintIgnoreRegex.search(comment)
    assert match is not None
    groups = match.groups()
    
    if rule_names is None:
        assert groups[1] is None
    else:
        assert groups[1] is not None  # FAILS when rule_names contains '['
```

**Failing input**: `directive='lint-ignore', rule_names=['[']`

## Reproducing the Bug

```python
import re

LintIgnoreRegex = re.compile(
    r"""
    \#\s*                   # leading hash and whitespace
    (lint-(?:ignore|fixme)) # directive
    (?:
        (?::\s*|\s+)        # separator
        (
            \w+             # first rule name
            (?:,\s*\w+)*    # subsequent rule names
        )
    )?                      # rule names are optional
    """,
    re.VERBOSE,
)

test_cases = [
    "# lint-ignore: [MyRule",
    "# lint-ignore: (Test)",
    "# lint-ignore: My-Rule",
]

for comment in test_cases:
    match = LintIgnoreRegex.search(comment)
    if match:
        directive, rules = match.groups()
        print(f"{comment!r} -> rules={rules!r}")

# Output:
# '# lint-ignore: [MyRule' -> rules=None
# '# lint-ignore: (Test)' -> rules=None  
# '# lint-ignore: My-Rule' -> rules='My'
```

## Why This Is A Bug

The regex uses `\w+` to match rule names, which only matches word characters `[a-zA-Z0-9_]`. When a rule name starts with a non-word character like `[`, the regex fails to capture ANY rule names and returns `None` for the second group.

In the `ignore_lint` method (rule.py:162-185), when `names is None`, the code treats this as "ignore all rules". This means a typo like `# lint-ignore: [TestRule` will cause ALL lint rules to be ignored instead of producing an error or being ignored itself.

## Fix

```diff
--- a/fixit/ftypes.py
+++ b/fixit/ftypes.py
@@ -69,11 +69,11 @@ LintIgnoreRegex = re.compile(
     r"""
     \#\s*                   # leading hash and whitespace
     (lint-(?:ignore|fixme)) # directive
     (?:
         (?::\s*|\s+)        # separator
         (
-            \w+             # first rule name
-            (?:,\s*\w+)*    # subsequent rule names
+            [^\s,]+         # first rule name (non-whitespace, non-comma)
+            (?:,\s*[^\s,]+)* # subsequent rule names
         )
     )?                      # rule names are optional
     """,
     re.VERBOSE,
 )
```

Alternative fix: Keep the strict regex but add validation in `ignore_lint` to warn when the directive appears malformed (has `:` but no captured rules).