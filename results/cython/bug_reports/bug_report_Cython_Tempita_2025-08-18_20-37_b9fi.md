# Bug Report: Cython.Tempita Multiple Template Processing Issues

**Target**: `Cython.Tempita`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

Found three distinct bugs in Cython.Tempita template processing: (1) None/True/False don't raise NameError when undefined, (2) empty expressions cause unhelpful SyntaxError, and (3) certain Unicode identifiers are incorrectly parsed.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import Cython.Tempita

@given(st.text().filter(lambda x: x.isidentifier() and x))
def test_undefined_variable_error(var_name):
    """Using undefined variable should raise NameError"""
    template = Cython.Tempita.Template(f"{{{{{var_name}}}}}")
    try:
        result = template.substitute()
        assert False, "Should have raised NameError"
    except NameError as e:
        assert var_name in str(e)
```

**Failing input**: `var_name='None'` (also fails for 'True', 'False')

## Reproducing the Bug

### Bug 1: None/True/False Don't Raise NameError

```python
import Cython.Tempita

template = Cython.Tempita.Template('{{None}}')
result = template.substitute()
print(f"Result: {repr(result)}")  # Returns '' instead of raising NameError

template2 = Cython.Tempita.Template('{{True}} {{False}}')
result2 = template2.substitute()
print(f"Result: {repr(result2)}")  # Returns 'True False' instead of raising NameError

# Compare with proper undefined variable
try:
    template3 = Cython.Tempita.Template('{{undefined}}')
    template3.substitute()
except NameError:
    print("undefined correctly raises NameError")
```

### Bug 2: Empty Expression Causes Unhelpful SyntaxError

```python
import Cython.Tempita

try:
    template = Cython.Tempita.Template('{{}}')
    result = template.substitute()
except SyntaxError as e:
    print(f"Empty expression error: {e}")  # "invalid syntax in expression: "
```

### Bug 3: Unicode Identifiers Incorrectly Parsed

```python
import Cython.Tempita

# º is a valid Python identifier
º = "test"
print(f"º.isidentifier() = {'º'.isidentifier()}")  # True

# But Tempita misparses it
try:
    template = Cython.Tempita.Template('{{º}}')
    result = template.substitute(**{'º': 'value'})
except NameError as e:
    print(f"Error: {e}")  # "name 'o' is not defined" - incorrectly parsed as 'o'

# Also fails for ª (parsed as 'a')
try:
    template = Cython.Tempita.Template('{{ª}}')
    result = template.substitute(**{'ª': 'value'})
except NameError as e:
    print(f"Error: {e}")  # "name 'a' is not defined"
```

## Why This Is A Bug

1. **None/True/False**: These should behave consistently with other undefined variables. When not provided in the namespace, they should raise NameError like any other undefined name, not silently return empty strings or default values.

2. **Empty expressions**: Should either be treated as literal text, return empty string, or provide a clear error message about empty expressions being invalid.

3. **Unicode identifiers**: Characters like º and ª are valid Python identifiers (per PEP 3131) and should be supported in template variable names. The parser incorrectly decomposes these characters.

## Fix

### Bug 1: None/True/False Handling
The template evaluator likely has special handling for Python built-ins. These should only be available if explicitly passed in the namespace:

```diff
# In the evaluation context setup
- namespace = {'None': None, 'True': True, 'False': False, ...}
+ namespace = {}  # Only include user-provided values
```

### Bug 2: Empty Expression Handling
Add validation for empty expressions:

```diff
# In expression parsing
  def parse_expr(expr):
+     if not expr.strip():
+         raise TemplateError("Empty expression not allowed")
      # rest of parsing logic
```

### Bug 3: Unicode Identifier Parsing
The parser needs proper Unicode normalization handling:

```diff
# In identifier tokenization
- # Current logic that decomposes º to 'o'
+ # Use proper Unicode category checking or Python's str.isidentifier()
+ if token.isidentifier():
+     return ('IDENTIFIER', token)
```