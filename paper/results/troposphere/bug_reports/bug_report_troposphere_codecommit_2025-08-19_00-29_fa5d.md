# Bug Report: troposphere Empty Title Validation Bypass

**Target**: `troposphere.codecommit.Repository`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The Repository class accepts empty string as a valid title, bypassing the alphanumeric validation that should reject non-alphanumeric or empty titles.

## Property-Based Test

```python
@given(st.text(min_size=0, max_size=100))
def test_repository_title_validation(title):
    """Repository title must be alphanumeric"""
    valid_pattern = re.compile(r"^[a-zA-Z0-9]+$")
    is_valid = bool(title and valid_pattern.match(title))
    
    try:
        repo = codecommit.Repository(
            title,
            RepositoryName="TestRepo"
        )
        assert is_valid, f"Expected invalid title '{title}' to raise error"
    except ValueError as e:
        assert not is_valid, f"Expected valid title '{title}' not to raise error"
        assert "not alphanumeric" in str(e)
```

**Failing input**: `title=''`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')
import troposphere.codecommit as codecommit

repo = codecommit.Repository(
    "",  # Empty title should be invalid
    RepositoryName="TestRepo"
)
print(f"Empty title was accepted: '{repo.title}'")
```

## Why This Is A Bug

The validate_title method in BaseAWSObject uses the regex pattern `^[a-zA-Z0-9]+$` which requires at least one alphanumeric character. However, the validation check `if not self.title or not valid_names.match(self.title)` has a logic issue: when title is an empty string, `not self.title` evaluates to True, but this should trigger the ValueError. The current implementation seems to have inverted logic or is missing proper empty string handling.

## Fix

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -325,7 +325,7 @@ class BaseAWSObject:
             % (self.__class__, self.title, name, type(value), expected_type)
         )
 
     def validate_title(self) -> None:
-        if not self.title or not valid_names.match(self.title):
+        if self.title is not None and (not self.title or not valid_names.match(self.title)):
             raise ValueError('Name "%s" not alphanumeric' % self.title)
```