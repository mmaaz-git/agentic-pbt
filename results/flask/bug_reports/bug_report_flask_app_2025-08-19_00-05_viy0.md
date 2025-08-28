# Bug Report: flask.app URL Rule Parameter Names Cannot Be Python Constants

**Target**: `flask.app.Flask.add_url_rule` / `werkzeug.routing.Rule`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

Flask/Werkzeug fails with an unclear error when trying to use Python constants (`False`, `True`, `None`) as parameter names in URL rules, while other Python keywords work fine.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from flask import Flask
import string

valid_identifiers = st.text(
    alphabet=string.ascii_letters + string.digits + '_',
    min_size=1,
    max_size=50
).filter(lambda s: s[0].isalpha() or s[0] == '_')

@given(param_name=valid_identifiers)
def test_url_parameter_names(param_name):
    app = Flask('test')
    rule = f'/test/<int:{param_name}>'
    
    def view_func(**kwargs):
        return 'ok'
    
    app.add_url_rule(rule, endpoint='test_endpoint', view_func=view_func)
```

**Failing input**: `param_name='False'` (also fails with `'True'` and `'None'`)

## Reproducing the Bug

```python
from flask import Flask

app = Flask('test')

@app.route('/test/<int:False>')
def view():
    return 'ok'
```

## Why This Is A Bug

While Python constants cannot be used as function parameter names, Flask should either:
1. Handle this gracefully by escaping/mangling these names internally, or
2. Provide a clear error message explaining the limitation

The current error "identifier field can't represent 'False' constant" is confusing and doesn't indicate that the issue is with the parameter name choice. Users may not realize that `False`, `True`, and `None` are special cases that fail while other Python keywords like `if`, `for`, `class` work fine.

## Fix

Provide a clearer error message in werkzeug/routing/rules.py when detecting Python constants as parameter names:

```diff
--- a/werkzeug/routing/rules.py
+++ b/werkzeug/routing/rules.py
@@ -834,6 +834,9 @@ class Rule:
         # In the compilation code where the error occurs
+        if name in ('True', 'False', 'None'):
+            raise ValueError(
+                f"Parameter name '{name}' cannot be a Python constant (True, False, None). "
+                f"Please choose a different parameter name."
+            )
         code = compile(module, "<werkzeug routing>", "exec")
```

Alternatively, implement name mangling to allow these names by prefixing them internally (e.g., `_param_False`) while maintaining the original name in the routing logic.