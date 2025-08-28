# Bug Report: sphinxcontrib-mermaid Invalid Mermaid Syntax from Special Class Names

**Target**: `sphinxcontrib.mermaid.autoclassdiag.class_diagram`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-01-18

## Summary

The `class_diagram` function in sphinxcontrib-mermaid generates invalid Mermaid syntax when Python classes have special characters in their names, particularly newlines and empty strings.

## Property-Based Test

```python
import sys
import types
from hypothesis import given, strategies as st

sys.path.insert(0, '/root/hypothesis-llm/envs/sphinxcontrib-mermaid_env/lib/python3.13/site-packages')
from sphinxcontrib.mermaid.autoclassdiag import class_diagram

@given(st.text())
def test_class_names_produce_valid_mermaid(class_name):
    """Test that any valid Python class name produces valid Mermaid syntax"""
    module = types.ModuleType("test_module")
    module.__name__ = "test_module"
    
    try:
        cls = type(class_name, (), {})
        cls.__module__ = "test_module"
        setattr(module, "TestClass", cls)
        
        child = type("Child", (cls,), {})
        child.__module__ = "test_module"
        module.Child = child
        
        sys.modules["test_module"] = module
        
        result = class_diagram("test_module", strict=False)
        
        # Check for invalid patterns
        lines = result.split('\n')
        for line in lines[1:]:  # Skip "classDiagram" header
            if " <|-- " in line:
                parts = line.strip().split(" <|-- ")
                assert len(parts) == 2, "Invalid inheritance syntax"
                assert parts[0], "Empty parent class name"
                assert parts[1], "Empty child class name"
    finally:
        if "test_module" in sys.modules:
            del sys.modules["test_module"]
```

**Failing input**: Empty string `""` and strings containing newlines like `"A\nB"`

## Reproducing the Bug

```python
import sys
import types

sys.path.insert(0, '/root/hypothesis-llm/envs/sphinxcontrib-mermaid_env/lib/python3.13/site-packages')
from sphinxcontrib.mermaid.autoclassdiag import class_diagram

# Bug 1: Empty class name
module1 = types.ModuleType("test_module1")
module1.__name__ = "test_module1"
EmptyName = type("", (), {})
EmptyName.__module__ = "test_module1"
module1.EmptyName = EmptyName
Child1 = type("Child", (EmptyName,), {})
Child1.__module__ = "test_module1"
module1.Child = Child1
sys.modules["test_module1"] = module1

result1 = class_diagram("test_module1", strict=False)
print("Empty name produces:")
print(result1)
# Output: Invalid syntax " <|-- Child" (missing parent name)

# Bug 2: Newline in class name
module2 = types.ModuleType("test_module2")
module2.__name__ = "test_module2"
NewlineClass = type("Class\nInjection", (), {})
NewlineClass.__module__ = "test_module2"
module2.NewlineClass = NewlineClass
Child2 = type("Child", (NewlineClass,), {})
Child2.__module__ = "test_module2"
module2.Child = Child2
sys.modules["test_module2"] = module2

result2 = class_diagram("test_module2", strict=False)
print("\nNewline in name produces:")
print(result2)
# Output: Broken diagram with inheritance split across lines
```

## Why This Is A Bug

The generated Mermaid diagrams are syntactically invalid and will fail to render properly. Mermaid expects inheritance relationships to be on a single line with both parent and child class names present. The current implementation doesn't sanitize or validate class names before including them in the diagram output, leading to:

1. Invalid syntax when class names are empty
2. Broken diagram structure when class names contain newlines
3. Potentially misleading diagrams with names containing Mermaid syntax characters

## Fix

```diff
--- a/sphinxcontrib/mermaid/autoclassdiag.py
+++ b/sphinxcontrib/mermaid/autoclassdiag.py
@@ -35,11 +35,20 @@ def class_diagram(*cls_or_modules, full=False, strict=False, namespace=None):
     inheritances = set()
 
     def get_tree(cls):
         for base in cls.__bases__:
             if base.__name__ == "object":
                 continue
             if namespace and not base.__module__.startswith(namespace):
                 continue
-            inheritances.add((base.__name__, cls.__name__))
+            
+            # Sanitize class names for Mermaid
+            parent_name = base.__name__.replace('\n', '_').replace('\r', '_')
+            child_name = cls.__name__.replace('\n', '_').replace('\r', '_')
+            
+            # Skip empty names as they produce invalid syntax
+            if not parent_name or not child_name:
+                continue
+                
+            inheritances.add((parent_name, child_name))
             if full:
                 get_tree(base)
```