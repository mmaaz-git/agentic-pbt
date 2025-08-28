# Bug Report: rpdk.java.utils.validate_codegen_model Accepts Input with Trailing Newline

**Target**: `rpdk.java.utils.validate_codegen_model`
**Severity**: Low
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `validate_codegen_model` function incorrectly accepts input values with trailing newlines (e.g., "1\n"), violating the stated regex pattern `^[1-2]$` which should only match exactly "1" or "2".

## Property-Based Test

```python
@given(st.sampled_from([" 1", "1 ", " 1 ", "\t1", "1\n", " 2 "]))
def test_validate_codegen_model_with_whitespace_padding(value):
    """Values with whitespace padding should be rejected"""
    validator = validate_codegen_model("1")
    
    with pytest.raises(WizardValidationError, match="Invalid selection"):
        validator(value)
```

**Failing input**: `"1\n"`

## Reproducing the Bug

```python
import sys
sys.path.append('/root/hypothesis-llm/envs/cloudformation-cli-java-plugin_env/lib/python3.13/site-packages')

from rpdk.java.utils import validate_codegen_model

validator = validate_codegen_model("1")
result = validator("1\n")
print(f"Accepted '1\\n' as valid, returned: {repr(result)}")
```

## Why This Is A Bug

The function uses the regex pattern `^[1-2]$` which should match only the exact strings "1" or "2". However, when using `re.match()` without the `re.MULTILINE` flag, the `$` anchor matches before a trailing newline, causing "1\n" and "2\n" to incorrectly pass validation.

## Fix

```diff
--- a/rpdk/java/utils.py
+++ b/rpdk/java/utils.py
@@ -142,7 +142,7 @@ def validate_codegen_model(default):
     def _validate_codegen_model(value):
         if not value:
             return default
 
-        match = re.match(pattern, value)
+        match = re.fullmatch(pattern, value)
         if not match:
             raise WizardValidationError("Invalid selection.")
 
         return value
```