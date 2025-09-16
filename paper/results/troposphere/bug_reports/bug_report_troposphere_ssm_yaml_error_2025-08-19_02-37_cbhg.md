# Bug Report: troposphere.validators.ssm YAML ReaderError Not Handled

**Target**: `troposphere.validators.ssm.validate_document_content`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-19

## Summary

The `validate_document_content` function crashes with `yaml.reader.ReaderError` when given strings containing special characters, instead of gracefully handling them and raising the expected `ValueError`.

## Property-Based Test

```python
from hypothesis import given, strategies as st, settings
import troposphere.validators.ssm as ssm_validators
import json
import yaml

@given(st.text())
@settings(max_examples=500)
def test_validate_document_content_malformed_json(text):
    """Test that malformed JSON/YAML strings are properly rejected"""
    # Skip if it's actually valid JSON or YAML
    try:
        json.loads(text)
        return  # It's valid JSON, skip
    except:
        pass
    
    try:
        yaml.safe_load(text)
        return  # It's valid YAML, skip
    except:
        pass
    
    # This should raise an error
    try:
        result = ssm_validators.validate_document_content(text)
        assert False, f"Should have rejected malformed JSON/YAML: {text!r}"
    except ValueError as e:
        assert "Content must be one of dict or json/yaml string" in str(e)
```

**Failing input**: `'\x1f'`

## Reproducing the Bug

```python
import troposphere.validators.ssm as ssm_validators

special_char = '\x1f'
result = ssm_validators.validate_document_content(special_char)
```

## Why This Is A Bug

The function's docstring and implementation suggest it should validate whether content is valid JSON, YAML, or a dict, and raise a `ValueError` with message "Content must be one of dict or json/yaml string" for invalid inputs. However, when the YAML parser encounters special characters, it raises `yaml.reader.ReaderError` which propagates up instead of being caught and handled properly. This violates the expected error contract of the function.

## Fix

```diff
--- a/troposphere/validators/ssm.py
+++ b/troposphere/validators/ssm.py
@@ -22,11 +22,14 @@ def validate_document_content(x):
             return False
 
     def check_yaml(x):
         import yaml
 
         try:
             yaml.safe_load(x)
             return True
-        except yaml.composer.ComposerError:
+        except (
+            yaml.composer.ComposerError,
+            yaml.reader.ReaderError,
+            yaml.scanner.ScannerError,
+        ):
             return False
 
     if isinstance(x, dict):
```