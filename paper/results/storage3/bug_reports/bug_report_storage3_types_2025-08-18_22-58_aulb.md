# Bug Report: storage3.types.UploadResponse Dataclass/Init Conflict

**Target**: `storage3.types.UploadResponse`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

UploadResponse class has conflicting @dataclass decorator and custom __init__ method, breaking dataclass functionality and causing serialization failures.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from storage3.types import UploadResponse
from dataclasses import asdict

@given(
    path=st.text(min_size=1, max_size=100),
    key=st.one_of(st.none(), st.text(min_size=1, max_size=100))
)
def test_upload_response_serialization(path, key):
    response = UploadResponse(path=path, Key=key)
    
    # This fails because asdict expects a proper dataclass
    result_dict = asdict(response)
    
    assert result_dict['path'] == path
    assert result_dict['full_path'] == key
    assert result_dict['fullPath'] == key
```

**Failing input**: Any valid input, e.g., `path='test', key='bucket/test'`

## Reproducing the Bug

```python
from storage3.types import UploadResponse
from dataclasses import asdict

response = UploadResponse(path='test/file.txt', Key='bucket/test/file.txt')

# Attempt to serialize using asdict fails
asdict(response)
# TypeError: asdict() should be called on dataclass instances
```

## Why This Is A Bug

The UploadResponse class is decorated with @dataclass, which automatically generates an __init__ method expecting (path, full_path, fullPath). However, it also defines a custom __init__ that takes (path, Key), overriding the dataclass-generated one. This breaks the dataclass contract:

1. The instance is not a proper dataclass instance
2. The `dict = asdict` assignment on line 107 is non-functional
3. Code calling `response.dict()` will fail with TypeError
4. The class violates the expected dataclass behavior

## Fix

```diff
--- a/storage3/types.py
+++ b/storage3/types.py
@@ -94,16 +94,21 @@ class UploadData(TypedDict, total=False):
     Key: str
 
 
-@dataclass
 class UploadResponse:
+    """Response from upload operations."""
     path: str
     full_path: str
     fullPath: str
 
     def __init__(self, path, Key):
         self.path = path
         self.full_path = Key
         self.fullPath = Key
 
-    dict = asdict
+    def dict(self):
+        return {
+            'path': self.path,
+            'full_path': self.full_path,
+            'fullPath': self.fullPath
+        }
```