# Bug Report: sphinxcontrib.mermaid.autoclassdiag Incorrect Exception Type for Edge Case Input

**Target**: `sphinxcontrib.mermaid.autoclassdiag.get_classes`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `get_classes` function raises `ValueError` instead of the expected `MermaidError` when given "." as input, violating its documented error handling contract.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from sphinxcontrib.mermaid.autoclassdiag import get_classes
from sphinxcontrib.mermaid.exceptions import MermaidError

@given(st.text())
def test_get_classes_invalid_names(name):
    """Test that get_classes raises MermaidError for invalid names"""
    assume(not name.startswith("sys"))
    assume(not name.startswith("os"))
    assume(not name.startswith("__"))
    assume(len(name) > 0)
    
    try:
        list(get_classes(name))
    except MermaidError:
        pass
    except Exception as e:
        if "No module named" not in str(e):
            raise
```

**Failing input**: `"."`

## Reproducing the Bug

```python
from sphinxcontrib.mermaid.autoclassdiag import get_classes
from sphinxcontrib.mermaid.exceptions import MermaidError

try:
    list(get_classes('.'))
except MermaidError as e:
    print(f"MermaidError raised (expected): {e}")
except ValueError as e:
    print(f"ValueError raised (BUG): {e}")
```

## Why This Is A Bug

The `get_classes` function is documented to raise `MermaidError` for invalid module/class names (line 20 of autoclassdiag.py catches ExtensionError and re-raises as MermaidError). However, when given "." as input, it raises `ValueError` instead. This violates the function's error handling contract and could cause unexpected failures in code that catches MermaidError specifically.

## Fix

```diff
--- a/sphinxcontrib/mermaid/autoclassdiag.py
+++ b/sphinxcontrib/mermaid/autoclassdiag.py
@@ -16,7 +16,7 @@ def get_classes(*cls_or_modules, strict=False):
     for cls_or_module in cls_or_modules:
         try:
             obj = import_object(cls_or_module)
-        except ExtensionError as e:
+        except (ExtensionError, ValueError) as e:
             raise MermaidError(str(e))
 
         if inspect.isclass(obj):
```