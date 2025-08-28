# Bug Report: flask.blueprints Path Handling Inconsistency

**Target**: `flask.blueprints.Blueprint`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

Flask Blueprint inconsistently handles relative paths for `static_folder` and `template_folder` parameters - `static_folder` is converted to an absolute path while `template_folder` remains relative.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import flask.blueprints as bp
import os
import string

@given(
    name=st.text(string.ascii_letters + string.digits + "_", min_size=1, max_size=50),
    static_folder=st.text(string.ascii_letters, min_size=1, max_size=20),
    template_folder=st.text(string.ascii_letters, min_size=1, max_size=20)
)
def test_blueprint_folder_path_inconsistency(name, static_folder, template_folder):
    blueprint = bp.Blueprint(
        name, 
        __name__,
        static_folder=static_folder,
        template_folder=template_folder
    )
    
    static_is_relative = not os.path.isabs(static_folder)
    template_is_relative = not os.path.isabs(template_folder)
    
    if static_is_relative and template_is_relative:
        static_became_absolute = os.path.isabs(blueprint.static_folder)
        template_became_absolute = os.path.isabs(blueprint.template_folder)
        
        assert static_became_absolute == template_became_absolute
```

**Failing input**: `name='test', static_folder='A', template_folder='A'`

## Reproducing the Bug

```python
import flask.blueprints as bp
import os

blueprint = bp.Blueprint(
    'test_blueprint',
    __name__,
    static_folder='static',
    template_folder='templates'
)

print(f"static_folder: {blueprint.static_folder}")
print(f"template_folder: {blueprint.template_folder}")
print(f"static is absolute: {os.path.isabs(blueprint.static_folder)}")
print(f"template is absolute: {os.path.isabs(blueprint.template_folder)}")
```

## Why This Is A Bug

This violates the principle of least surprise and API consistency. When providing relative paths for both `static_folder` and `template_folder`, users would expect them to be handled identically. The current behavior converts only `static_folder` to an absolute path, creating an inconsistent API where similar parameters are treated differently without clear documentation of this distinction.

## Fix

The issue stems from how `flask.sansio.scaffold.Scaffold` handles these paths differently. The fix would ensure consistent treatment:

```diff
class Scaffold:
    def __init__(self, ...):
        ...
        if static_folder is not None:
            static_folder = os.fspath(static_folder).rstrip(r"\/")
            if not os.path.isabs(static_folder):
                static_folder = os.path.join(root_path, static_folder)
        
        self.static_folder = static_folder
-       self.template_folder = template_folder
+       
+       if template_folder is not None:
+           template_folder = os.fspath(template_folder).rstrip(r"\/")
+           if not os.path.isabs(template_folder):
+               template_folder = os.path.join(root_path, template_folder)
+       
+       self.template_folder = template_folder
```

Alternatively, both could remain relative, but consistency should be maintained.