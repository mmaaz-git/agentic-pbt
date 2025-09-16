# Bug Report: fire.interact Comma in Variable Names Breaks Output Parsing

**Target**: `fire.interact._AvailableString`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `_AvailableString` function in `fire.interact` uses commas as separators in its output without escaping or filtering variable names containing commas, creating ambiguous output that cannot be reliably parsed.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')
from fire import interact

@given(st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='_'), min_size=1, max_size=10))
def test_comma_in_variable_names(base_name):
    var_with_comma = base_name + ',' + base_name
    variables = {'normal_var': 1, var_with_comma: 2, 'another_var': 3}
    output = interact._AvailableString(variables, verbose=False)
    
    lines = output.split('\n')
    for line in lines:
        if 'Objects:' in line and ':' in line:
            items_str = line.split(':', 1)[1].strip()
            parsed_items = [item.strip() for item in items_str.split(',')]
            expected_items = {'normal_var', var_with_comma, 'another_var'}
            parsed_set = set(parsed_items)
            assert parsed_set == expected_items, f"Comma in variable name breaks parsing"
```

**Failing input**: `base_name='0'` (creates variable name `'0,0'`)

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')
from fire import interact

variables = {
    'var_a': 1,
    'var,b': 2,
    'var_c': 3
}

output = interact._AvailableString(variables, verbose=False)
print(output)

lines = output.split('\n')
for line in lines:
    if 'Objects:' in line:
        items_str = line.split(':', 1)[1].strip()
        parsed_vars = [item.strip() for item in items_str.split(',')]
        print("Original variables:", set(variables.keys()))
        print("Parsed variables:", set(parsed_vars))
```

## Why This Is A Bug

The function uses comma as a separator when joining variable names but doesn't handle the case where variable names themselves contain commas. Python allows commas in variable names (e.g., `globals()['var,name'] = 1`), so when `_AvailableString` outputs "Objects: var,b, var_c", it's impossible to determine if this represents two variables (`var,b` and `var_c`) or three variables (`var`, `b`, and `var_c`). This ambiguity breaks any code trying to parse the output.

## Fix

```diff
--- a/fire/interact.py
+++ b/fire/interact.py
@@ -53,8 +53,10 @@ def _AvailableString(variables, verbose=False):
   modules = []
   other = []
   for name, value in variables.items():
     if not verbose and name.startswith('_'):
       continue
+    # Filter out variable names with commas to avoid ambiguous output
+    if ',' in name:
+      continue
     if '-' in name or '/' in name:
       continue
 
     if inspect.ismodule(value):
```