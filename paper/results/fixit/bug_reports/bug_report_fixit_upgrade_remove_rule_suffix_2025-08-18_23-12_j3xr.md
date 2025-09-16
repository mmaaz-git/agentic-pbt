# Bug Report: FixitRemoveRuleSuffix Creates Invalid Python with Reserved Keywords

**Target**: `fixit.upgrade.remove_rule_suffix.FixitRemoveRuleSuffix`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The FixitRemoveRuleSuffix lint rule removes "Rule" suffix from class names without checking if the resulting name is a Python reserved keyword, producing syntactically invalid code.

## Property-Based Test

```python
@given(
    class_name=st.text(
        alphabet=st.characters(whitelist_categories=["Lu", "Ll"], min_codepoint=65, max_codepoint=122),
        min_size=5,
        max_size=30
    ).filter(lambda x: x[0].isupper() and x.isidentifier() and not x in ['Rule', 'class', 'def', 'import', 'from', 'if', 'else', 'elif', 'for', 'while', 'try', 'except'])
)
def test_remove_rule_suffix_idempotence(class_name):
    class_name_with_rule = class_name + "Rule"
    
    code = f"""
from fixit import LintRule

class {class_name_with_rule}(LintRule):
    pass
"""
    
    path = Path.cwd() / "test.py"
    config = Config(path=path)
    runner = LintRunner(path, code.encode())
    rule = FixitRemoveRuleSuffix()
    
    reports = list(runner.collect_violations([rule], config))
    
    if reports:
        first_result = runner.apply_replacements(reports).bytes.decode()
        
        runner2 = LintRunner(path, first_result.encode())
        reports2 = list(runner2.collect_violations([rule], config))
        
        assert len(reports2) == 0, f"Rule is not idempotent for {class_name_with_rule}"
```

**Failing input**: `class_name='False'`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fixit_env/lib/python3.13/site-packages')

from pathlib import Path
from fixit.upgrade.remove_rule_suffix import FixitRemoveRuleSuffix
from fixit.engine import LintRunner
from fixit.ftypes import Config
import libcst as cst

code = """
from fixit import LintRule

class FalseRule(LintRule):
    pass
"""

path = Path.cwd() / "test.py"
config = Config(path=path)
runner = LintRunner(path, code.encode())
rule = FixitRemoveRuleSuffix()

reports = list(runner.collect_violations([rule], config))
result = runner.apply_replacements(reports).bytes.decode()

print("Result:", result)

try:
    cst.parse_module(result)
except Exception as e:
    print(f"Invalid Python generated: {e}")
```

## Why This Is A Bug

The rule transforms `class FalseRule(LintRule)` into `class False(LintRule)`, but `False` is a Python keyword and cannot be used as a class name. This produces syntactically invalid Python code that cannot be parsed or executed. The same issue occurs with other Python keywords like `TrueRule`, `NoneRule`, `PassRule`, etc.

## Fix

```diff
--- a/fixit/upgrade/remove_rule_suffix.py
+++ b/fixit/upgrade/remove_rule_suffix.py
@@ -3,6 +3,7 @@
 # This source code is licensed under the MIT license found in the
 # LICENSE file in the root directory of this source tree.
 
+import keyword
 import libcst
 from libcst.metadata import FullyQualifiedNameProvider
 
@@ -59,5 +60,9 @@ class FixitRemoveRuleSuffix(LintRule):
                 if qname == "fixit.LintRule":
                     rule_name = node.name.value
                     if rule_name.endswith("Rule"):
-                        rep = node.name.with_changes(value=rule_name[:-4])
-                        self.report(node.name, replacement=rep)
+                        new_name = rule_name[:-4]
+                        # Don't remove suffix if it would create a reserved keyword
+                        if not keyword.iskeyword(new_name):
+                            rep = node.name.with_changes(value=new_name)
+                            self.report(node.name, replacement=rep)
```