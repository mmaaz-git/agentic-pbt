# Bug Report: quickbooks.utils Incorrect SQL Quote Escaping

**Target**: `quickbooks.utils.build_where_clause` and `quickbooks.utils.build_choose_clause`
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The functions `build_where_clause` and `build_choose_clause` use incorrect SQL escaping by replacing single quotes with backslash-quote (`\'`) instead of the SQL-92 standard of doubling quotes (`''`), potentially causing SQL errors and security vulnerabilities.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from quickbooks.utils import build_where_clause

@given(st.text(min_size=1).filter(lambda x: "'" in x))
def test_sql_standard_quote_escaping(text):
    result = build_where_clause(field=text)
    
    # SQL standard requires doubling quotes, not backslash escaping
    correct_escaped = text.replace("'", "''")
    correct_result = f"field = '{correct_escaped}'"
    
    # The function incorrectly uses backslash escaping
    assert r"\'" in result
    assert result != correct_result
```

**Failing input**: `"O'Brien"`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/python-quickbooks_env/lib/python3.13/site-packages')

from quickbooks.utils import build_where_clause, build_choose_clause

# Test 1: Simple apostrophe
name = "O'Brien"
result = build_where_clause(LastName=name)
print(f"Got:      {result}")
print(f"Expected: LastName = 'O''Brien'")

# Test 2: Multiple quotes
text = "'''"
result = build_where_clause(field=text)
print(f"Got:      {result}")
print(f"Expected: field = ''''''''")

# Test 3: build_choose_clause
choices = ["O'Brien", "John's"]
result = build_choose_clause(choices, "LastName")
print(f"Got:      {result}")
print(f"Expected: LastName in ('O''Brien', 'John''s')")
```

## Why This Is A Bug

This violates SQL-92 standard for string literals. Most SQL databases (PostgreSQL, MySQL in ANSI mode, Oracle, SQL Server) expect single quotes to be escaped by doubling them (`''`), not with backslash (`\'`). Using backslash escaping can cause:

1. **SQL syntax errors** in standard-compliant databases
2. **Security vulnerabilities** if the database doesn't properly handle backslash escaping
3. **Compatibility issues** across different SQL engines (only MySQL in non-ANSI mode accepts `\'`)

## Fix

```diff
--- a/quickbooks/utils.py
+++ b/quickbooks/utils.py
@@ -6,7 +6,7 @@ def build_where_clause(**kwargs):
 
         for key, value in kwargs.items():
             if isinstance(value, str):
-                where.append("{0} = '{1}'".format(key, value.replace(r"'", r"\'")))
+                where.append("{0} = '{1}'".format(key, value.replace("'", "''")))
             else:
                 where.append("{0} = {1}".format(key, value))
 
@@ -23,7 +23,7 @@ def build_choose_clause(choices, field):
 
         for choice in choices:
             if isinstance(choice, str):
-                where.append("'{0}'".format(choice.replace(r"'", r"\'")))
+                where.append("'{0}'".format(choice.replace("'", "''")))
             else:
                 where.append("{0}".format(choice))
```