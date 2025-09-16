# Bug Report: troposphere.comprehend Empty String Title Bypasses Validation

**Target**: `troposphere.comprehend.DocumentClassifier` (and all other AWSObject subclasses)
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

Empty strings bypass title validation in AWS CloudFormation objects, allowing creation of resources with invalid empty titles when alphanumeric titles are required.

## Property-Based Test

```python
@given(st.text())
def test_aws_object_title_validation(title):
    """Test that AWS objects validate titles correctly"""
    import re
    valid_names = re.compile(r"^[a-zA-Z0-9]+$")
    
    if title and valid_names.match(title):
        # Should succeed
        obj = DocumentClassifier(title, DataAccessRoleArn="arn", 
                                DocumentClassifierName="test",
                                InputDataConfig=DocumentClassifierInputDataConfig(),
                                LanguageCode="en")
        assert obj.title == title
    else:
        # Should fail
        with pytest.raises(ValueError, match='Name ".*" not alphanumeric'):
            DocumentClassifier(title, DataAccessRoleArn="arn",
                             DocumentClassifierName="test", 
                             InputDataConfig=DocumentClassifierInputDataConfig(),
                             LanguageCode="en")
```

**Failing input**: `''` (empty string)

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.comprehend import DocumentClassifier, DocumentClassifierInputDataConfig

obj = DocumentClassifier("", 
                        DataAccessRoleArn="arn",
                        DocumentClassifierName="test",
                        InputDataConfig=DocumentClassifierInputDataConfig(),
                        LanguageCode="en")
print(f"Created object with empty title: {obj.title!r}")
```

## Why This Is A Bug

The `validate_title()` method is designed to ensure titles are alphanumeric (matching `^[a-zA-Z0-9]+$`). However, the validation is only called when the title is truthy. In `__init__.py` line 183-184:

```python
if self.title:
    self.validate_title()
```

This means empty strings completely bypass validation, violating the documented contract that titles must be alphanumeric. Empty strings are not valid CloudFormation resource names and should be rejected.

## Fix

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -180,8 +180,8 @@ class BaseAWSObject:
         ]
 
         # try to validate the title if its there
-        if self.title:
-            self.validate_title()
+        if self.title is not None:
+            self.validate_title()
 
         # Create the list of properties set on this object by the user
         self.properties = {}
```