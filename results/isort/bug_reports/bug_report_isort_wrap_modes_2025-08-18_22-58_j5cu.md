# Bug Report: isort.wrap_modes Empty Import Handling Errors

**Target**: `isort.wrap_modes`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

Multiple wrap mode formatters in isort incorrectly handle empty import lists, either returning malformed output with unbalanced parentheses or non-empty strings when they should return empty strings.

## Property-Based Test

```python
@given(st.lists(st.text(min_size=1)))
def test_empty_imports_invariant(imports_list):
    interface = {
        "statement": "from module import ",
        "imports": imports_list.copy(),
        "white_space": "    ",
        "indent": "    ",
        "line_length": 80,
        "comments": [],
        "line_separator": "\n",
        "comment_prefix": " #",
        "include_trailing_comma": False,
        "remove_comments": False,
    }
    
    for formatter_name in wrap_modes._wrap_modes:
        if formatter_name == "VERTICAL_GRID_GROUPED_NO_COMMA":
            continue
        formatter = wrap_modes._wrap_modes[formatter_name]
        result = formatter(**interface.copy())
        
        if not imports_list:
            assert result == "", f"{formatter_name} should return empty string for empty imports"
            assert result.count('(') == result.count(')'), f"{formatter_name} has unbalanced parentheses"
```

**Failing input**: `imports_list=[]`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, "/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages")
import isort.wrap_modes as wrap_modes

interface = {
    "statement": "from module import ",
    "imports": [],
    "white_space": "    ",
    "indent": "    ",
    "line_length": 80,
    "comments": [],
    "line_separator": "\n",
    "comment_prefix": " #",
    "include_trailing_comma": False,
    "remove_comments": False,
}

# Bug 1: VERTICAL_HANGING_INDENT returns non-empty for empty imports
result = wrap_modes.vertical_hanging_indent(**interface.copy())
print(f"VERTICAL_HANGING_INDENT: {repr(result)}")
assert result == "", f"Expected empty, got {repr(result)}"

# Bug 2: VERTICAL_GRID returns unbalanced parentheses
result = wrap_modes.vertical_grid(**interface.copy())
print(f"VERTICAL_GRID: {repr(result)}")
assert result == "" or result.count('(') == result.count(')'), f"Unbalanced parentheses: {repr(result)}"

# Bug 3: VERTICAL_GRID_GROUPED returns unbalanced parentheses  
result = wrap_modes.vertical_grid_grouped(**interface.copy())
print(f"VERTICAL_GRID_GROUPED: {repr(result)}")
assert result == "" or result.count('(') == result.count(')'), f"Unbalanced parentheses: {repr(result)}"
```

## Why This Is A Bug

These formatters violate the invariant that wrap mode functions should return an empty string when given an empty imports list (as most other formatters correctly do). Additionally, returning unbalanced parentheses creates syntactically invalid Python code. The functions should check if the imports list is empty before processing, similar to how other formatters like `grid`, `vertical`, and `hanging_indent` do.

## Fix

```diff
--- a/isort/wrap_modes.py
+++ b/isort/wrap_modes.py
@@ -169,6 +169,8 @@
 @_wrap_mode
 def vertical_hanging_indent(**interface: Any) -> str:
+    if not interface["imports"]:
+        return ""
     _line_with_comments = isort.comments.add_to_line(
         interface["comments"],
         "",
@@ -221,6 +223,8 @@
 @_wrap_mode
 def vertical_grid(**interface: Any) -> str:
+    if not interface["imports"]:
+        return ""
     return _vertical_grid_common(need_trailing_char=True, **interface) + ")"
 
 
 @_wrap_mode
 def vertical_grid_grouped(**interface: Any) -> str:
+    if not interface["imports"]:
+        return ""
     return (
         _vertical_grid_common(need_trailing_char=False, **interface)
         + str(interface["line_separator"])
```