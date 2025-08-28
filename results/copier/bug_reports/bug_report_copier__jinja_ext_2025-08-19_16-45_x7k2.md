# Bug Report: copier._jinja_ext Template Re-rendering Raises Incorrect MultipleYieldTagsError

**Target**: `copier._jinja_ext.YieldExtension`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

Templates with a single `{% yield %}` tag incorrectly raise `MultipleYieldTagsError` when rendered more than once with the same template instance.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from copier._jinja_ext import YieldEnvironment, YieldExtension
from copier.errors import MultipleYieldTagsError

@given(
    var_name=st.from_regex(r"[a-zA-Z_][a-zA-Z0-9_]*", fullmatch=True),
    iterable_name=st.from_regex(r"[a-zA-Z_][a-zA-Z0-9_]*", fullmatch=True),
    first_iterable=st.lists(st.integers(), min_size=0, max_size=5),
    second_iterable=st.lists(st.integers(), min_size=0, max_size=5)
)
def test_template_rerender_bug(var_name, iterable_name, first_iterable, second_iterable):
    if var_name == iterable_name:
        return
    
    env = YieldEnvironment(extensions=[YieldExtension])
    template_str = f"{{% yield {var_name} from {iterable_name} %}}content{{% endyield %}}"
    template = env.from_string(template_str)
    
    # First render works
    result1 = template.render({iterable_name: first_iterable})
    
    # Second render fails with MultipleYieldTagsError
    try:
        result2 = template.render({iterable_name: second_iterable})
        assert False, "Expected MultipleYieldTagsError"
    except MultipleYieldTagsError:
        pass  # Bug confirmed
```

**Failing input**: Any valid input triggers the bug on second render, e.g., `var_name='item'`, `iterable_name='items'`, `first_iterable=[1]`, `second_iterable=[2]`

## Reproducing the Bug

```python
from copier._jinja_ext import YieldEnvironment, YieldExtension
from copier.errors import MultipleYieldTagsError

env = YieldEnvironment(extensions=[YieldExtension])
template = env.from_string("{% yield item from items %}content{% endyield %}")

result1 = template.render({"items": [1, 2]})
print(f"First render: {result1}")

try:
    result2 = template.render({"items": [3, 4]})
    print(f"Second render: {result2}")
except MultipleYieldTagsError as e:
    print(f"BUG: {e}")
```

## Why This Is A Bug

The error message states "Only one yield tag is allowed per path name" but the template contains exactly one yield tag. The error occurs because the `YieldExtension._yield_support` method checks if `yield_name` or `yield_iterable` are already set in the environment (lines 104-107) and raises an error if they are. These attributes are set during the first render but never reset before the second render, causing the false positive.

This violates the expected behavior that Jinja2 templates can be rendered multiple times with different contexts.

## Fix

```diff
--- a/copier/_jinja_ext.py
+++ b/copier/_jinja_ext.py
@@ -95,6 +95,10 @@ class YieldExtension(Extension):
 
     def _yield_support(
         self, yield_name: str, yield_iterable: Iterable[Any], caller: Callable[[], str]
     ) -> str:
         """Support function for the yield tag.
 
         Sets the `yield_name` and `yield_iterable` attributes in the environment then calls
         the provided caller function. If an UndefinedError is raised, it returns an empty string.
         """
         if (
             self.environment.yield_name is not None
             or self.environment.yield_iterable is not None
         ):
-            raise MultipleYieldTagsError(
-                "Attempted to parse the yield tag twice. Only one yield tag is allowed per path name.\n"
-                f'A yield tag with the name: "{self.environment.yield_name}" and iterable: "{self.environment.yield_iterable}" already exists.'
-            )
+            # Reset the attributes if they're from a previous render
+            if self.environment.yield_name != yield_name or self.environment.yield_iterable is not yield_iterable:
+                self.environment.yield_name = None
+                self.environment.yield_iterable = None
+            else:
+                raise MultipleYieldTagsError(
+                    "Attempted to parse the yield tag twice. Only one yield tag is allowed per path name.\n"
+                    f'A yield tag with the name: "{self.environment.yield_name}" and iterable: "{self.environment.yield_iterable}" already exists.'
+                )
 
         self.environment.yield_name = yield_name
         self.environment.yield_iterable = yield_iterable
```

Alternative fix: Reset the attributes at the start of each render cycle, possibly in the template's render method or by hooking into Jinja2's rendering lifecycle properly.