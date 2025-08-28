# Bug Report: jurigged.parse Missing Variable Reads in Augmented Assignments

**Target**: `jurigged.parse.variables`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The `variables` function in `jurigged.parse` fails to track variable reads in augmented assignment operations (+=, -=, *=, etc.), only tracking them as assignments despite these operations inherently reading the variable first.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import ast
from jurigged.parse import variables

def python_identifier():
    first_char = st.sampled_from('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_')
    other_chars = st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_', min_size=0, max_size=10)
    return st.builds(lambda f, o: f + o, first_char, other_chars).filter(
        lambda x: x not in ['False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await', 
                           'break', 'class', 'continue', 'def', 'del', 'elif', 'else', 'except',
                           'finally', 'for', 'from', 'global', 'if', 'import', 'in', 'is', 
                           'lambda', 'nonlocal', 'not', 'or', 'pass', 'raise', 'return', 
                           'try', 'while', 'with', 'yield']
    )

@given(var_name=python_identifier())
def test_augmented_assignment(var_name):
    code = f"{var_name} += 1"
    tree = ast.parse(code)
    result = variables(tree, {})
    
    # Augmented assignment both reads and writes
    assert var_name in result.read, f"{var_name} should be in read set for augmented assignment"
    assert var_name in result.free, f"{var_name} should be free (read but not yet assigned)"
```

**Failing input**: `var_name='a'` (any valid identifier fails)

## Reproducing the Bug

```python
import ast
from jurigged.parse import variables

# Augmented assignment
code1 = "x += 1"
tree1 = ast.parse(code1)
result1 = variables(tree1, {})
print(f"x += 1 -> Assigned: {result1.assigned}, Read: {result1.read}")

# Equivalent regular assignment for comparison
code2 = "x = x + 1"
tree2 = ast.parse(code2)
result2 = variables(tree2, {})
print(f"x = x + 1 -> Assigned: {result2.assigned}, Read: {result2.read}")
```

## Why This Is A Bug

Augmented assignments like `x += 1` are syntactic sugar for `x = x + 1`, which means they read the current value of `x` before assigning the new value. The parser correctly handles `x = x + 1` by marking `x` as both assigned and read, but fails to recognize the implicit read in `x += 1`. This leads to incorrect free variable analysis - variables that should be considered free (used before assignment) are missed.

## Fix

```diff
--- a/jurigged/parse.py
+++ b/jurigged/parse.py
@@ -76,6 +76,16 @@ def variables(node: ast.Name, mapping):
         return Variables(read={node.id})
 
 
+@ovld
+def variables(node: ast.AugAssign, mapping):
+    # Augmented assignment both reads and assigns the target
+    target_vars = recurse(node.target, mapping)
+    value_vars = recurse(node.value, mapping)
+    # The target is both read and assigned
+    if isinstance(node.target, ast.Name):
+        return Variables(assigned={node.target.id}, read={node.target.id}) | value_vars
+    return target_vars | value_vars
+
 @ovld
 def variables(node: ast.AST, mapping):
     return recurse(list(ast.iter_child_nodes(node)), mapping)
```