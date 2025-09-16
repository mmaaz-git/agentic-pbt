# Bug Report: troposphere.BaseAWSObject Title Validation Bypass

**Target**: `troposphere.BaseAWSObject`
**Severity**: Medium  
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

Empty strings and None values bypass title validation in BaseAWSObject, allowing invalid resource names that should be rejected according to the alphanumeric validation rule.

## Property-Based Test

```python
@given(st.text())
def test_title_validation(title):
    import re
    valid_names = re.compile(r"^[a-zA-Z0-9]+$")
    is_valid = bool(title and valid_names.match(title))
    
    try:
        cluster = pcs.Cluster(
            title,
            Networking=pcs.Networking(SubnetIds=["subnet-123"]),
            Scheduler=pcs.Scheduler(Type="SLURM", Version="23.11"),
            Size="SMALL"
        )
        assert is_valid, f"Invalid title '{title}' was accepted"
    except ValueError as e:
        assert not is_valid, f"Valid title '{title}' was rejected"
        assert "not alphanumeric" in str(e)
```

**Failing input**: `''` (empty string)

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')
import troposphere.pcs as pcs

cluster = pcs.Cluster(
    "",
    Networking=pcs.Networking(SubnetIds=["subnet-123"]),
    Scheduler=pcs.Scheduler(Type="SLURM", Version="23.11"),
    Size="SMALL"
)
cluster.to_dict()
print(f"Empty title accepted: '{cluster.title}'")
```

## Why This Is A Bug

The validate_title method is designed to ensure resource titles are alphanumeric only. However, the validation is conditionally executed only when title is truthy (line 183: `if self.title:`). This allows empty strings and None values to bypass validation entirely, violating the intended alphanumeric-only constraint.

## Fix

```diff
# In BaseAWSObject.__init__
-       # try to validate the title if its there
-       if self.title:
-           self.validate_title()
+       # Always validate the title
+       self.validate_title()

# In validate_title method
    def validate_title(self) -> None:
-       if not self.title or not valid_names.match(self.title):
+       if self.title is not None and (not self.title or not valid_names.match(self.title)):
            raise ValueError('Name "%s" not alphanumeric' % self.title)
```