# Bug Report: rpdk.java.resolver.translate_type AttributeError with None Inner Type

**Target**: `rpdk.java.resolver.translate_type`
**Severity**: High
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `translate_type` function crashes with an AttributeError when processing a container type with None as the inner type, failing to handle this edge case gracefully.

## Property-Based Test

```python
def test_translate_type_with_none_type():
    """Test translate_type with None as inner type"""
    resolved = ResolvedType(ContainerType.LIST, None)
    
    try:
        result = translate_type(resolved)
        assert "List<" in result
    except (AttributeError, TypeError) as e:
        pytest.fail(f"translate_type failed with None inner type: {e}")
```

**Failing input**: `ResolvedType(ContainerType.LIST, None)`

## Reproducing the Bug

```python
import sys
sys.path.append('/root/hypothesis-llm/envs/cloudformation-cli-java-plugin_env/lib/python3.13/site-packages')

from rpdk.java.resolver import translate_type
from rpdk.core.jsonutils.resolver import ResolvedType, ContainerType

resolved = ResolvedType(ContainerType.LIST, None)
result = translate_type(resolved)
```

## Why This Is A Bug

The function should handle None inner types gracefully, either by returning a sensible default (like "List<Object>") or raising a more descriptive error. Instead, it crashes with AttributeError when trying to access `resolved_type.type.container` where `resolved_type.type` is None.

## Fix

```diff
--- a/rpdk/java/resolver.py
+++ b/rpdk/java/resolver.py
@@ -35,6 +35,9 @@ def translate_type(resolved_type):
     if resolved_type.container == ContainerType.MULTIPLE:
         return "Object"
 
+    if resolved_type.type is None:
+        return f"{resolved_type.container.name.capitalize()}<Object>"
+
     item_type = translate_type(resolved_type.type)
 
     if resolved_type.container == ContainerType.DICT:
```