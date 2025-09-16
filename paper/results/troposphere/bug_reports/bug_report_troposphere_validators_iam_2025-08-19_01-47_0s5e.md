# Bug Report: troposphere.validators.iam Multiple Validation Bugs

**Target**: `troposphere.validators.iam`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

Found three bugs in troposphere IAM validators: incorrect error message for group names, and format string bugs in path and user name validators.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from troposphere.validators import iam as iam_validators
import pytest

@given(st.text(min_size=129, max_size=200))
def test_iam_group_name_error_message_bug(name):
    """Check if error message for group name says 'Role Name' instead of 'Group Name'"""
    with pytest.raises(ValueError) as exc_info:
        iam_validators.iam_group_name(name)
    error_msg = str(exc_info.value)
    assert "IAM Role Name may not exceed 128 characters" in error_msg

@given(st.text(min_size=513, max_size=600))
def test_iam_path_format_string_bug(path):
    """Test if iam_path has a format string bug in error message"""
    with pytest.raises(ValueError) as exc_info:
        iam_validators.iam_path(path)
    assert isinstance(exc_info.value.args, tuple) and len(exc_info.value.args) == 2

@given(st.text())
def test_iam_user_name_invalid_format_bug(name):
    """Test format string in invalid user name error"""
    assume(name and len(name) <= 64)
    assume(not re.match(r"^[\w+=,.@-]+$", name))
    with pytest.raises(ValueError) as exc_info:
        iam_validators.iam_user_name(name)
    assert isinstance(exc_info.value.args, tuple) and len(exc_info.value.args) == 2
```

**Failing input**: Group name: `"a" * 129`, Path: `"/" + "a" * 511 + "/"`, User name: `"user$name"`

## Reproducing the Bug

```python
from troposphere.validators import iam as iam_validators

# Bug 1: Incorrect error message for group names
try:
    iam_validators.iam_group_name("a" * 129)
except ValueError as e:
    print(f"Error: {e}")
    # Output: IAM Role Name may not exceed 128 characters

# Bug 2: Format string bug in path validator
try:
    iam_validators.iam_path("/" + "a" * 511 + "/")
except ValueError as e:
    print(f"Args: {e.args}")
    # Output: ('IAM path %s may not exceed 512 characters', '/aaa.../')

# Bug 3: Format string bug in user name validator
try:
    iam_validators.iam_user_name("user$name")
except ValueError as e:
    print(f"Args: {e.args}")
    # Output: ("%s is not a valid value for AWS::IAM::User property 'UserName'", 'user$name')
```

## Why This Is A Bug

1. The group name validator incorrectly reports "IAM Role Name" in its error message when validating group names, causing confusion.
2. The path and user name validators don't properly format their error messages, creating tuples instead of formatted strings.

## Fix

```diff
--- a/troposphere/validators/iam.py
+++ b/troposphere/validators/iam.py
@@ -17,7 +17,7 @@ def iam_group_name(group_name):
     Property: Group.GroupName
     """
     if len(group_name) > 128:
-        raise ValueError("IAM Role Name may not exceed 128 characters")
+        raise ValueError("IAM Group Name may not exceed 128 characters")
     iam_names(group_name)
     return group_name
 
@@ -39,7 +39,7 @@ def iam_path(path):
     Property: User.Path
     """
     if len(path) > 512:
-        raise ValueError("IAM path %s may not exceed 512 characters", path)
+        raise ValueError("IAM path %s may not exceed 512 characters" % path)
 
     iam_path_re = re.compile(r"^\/.*\/$|^\/$")
     if not iam_path_re.match(path):
@@ -74,7 +74,7 @@ def iam_user_name(user_name):
         return user_name
     else:
         raise ValueError(
-            "%s is not a valid value for AWS::IAM::User property 'UserName'", user_name
+            "%s is not a valid value for AWS::IAM::User property 'UserName'" % user_name
         )
```