# Bug Report: jurigged.rescript.redirector_code SyntaxError with Python Keywords

**Target**: `jurigged.rescript.redirector_code`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-19

## Summary

The `redirector_code()` function crashes with a SyntaxError when passed Python keywords as the `name` parameter, attempting to create functions with invalid names.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import jurigged.rescript as rescript

@given(
    name=st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll'), min_codepoint=97, max_codepoint=122),
        min_size=1,
        max_size=20
    ).filter(lambda x: x.isidentifier() and not x.startswith('_'))
)
def test_redirector_code_generates_valid_code(name):
    code_obj = rescript.redirector_code(name)
    assert isinstance(code_obj, types.CodeType)
    assert code_obj.co_name == name
```

**Failing input**: `'if'`

## Reproducing the Bug

```python
import jurigged.rescript as rescript

code_obj = rescript.redirector_code('if')
```

## Why This Is A Bug

The function generates Python code dynamically using string formatting without validating that the name is not a Python keyword. When a keyword like 'if', 'for', or 'class' is passed, it attempts to create a function definition like `def if(*args, **kwargs):` which is syntactically invalid Python code.

## Fix

```diff
--- a/jurigged/rescript.py
+++ b/jurigged/rescript.py
@@ -1,6 +1,7 @@
 import ast
 import io
 import types
+import keyword
 
 
 def split_script(script):  # pragma: no cover
@@ -61,6 +62,9 @@ def redirector_code(name):
     That code object is meant to be patched onto an existing function so that it
     can redirect to something else.
     """
+    if keyword.iskeyword(name):
+        raise ValueError(f"Cannot create redirector for Python keyword: {name}")
+    
     glb = {}
     exec(redirector.format(name=name), glb)
     fn = glb[name]
```