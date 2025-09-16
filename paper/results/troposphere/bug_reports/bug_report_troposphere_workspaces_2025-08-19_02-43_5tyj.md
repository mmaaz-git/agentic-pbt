# Bug Report: troposphere.workspaces Round-Trip Property Violation

**Target**: `troposphere.workspaces` (AWSObject classes)
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `to_dict()` and `from_dict()` methods in AWSObject classes (Workspace, ConnectionAlias, WorkspacesPool) violate the round-trip property: `from_dict(title, obj.to_dict())` fails because `to_dict()` wraps properties in a 'Properties' key while `from_dict()` expects unwrapped properties.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.workspaces as ws

@given(
    bundle_id=st.text(min_size=1, max_size=100),
    directory_id=st.text(min_size=1, max_size=100),
    username=st.text(min_size=1, max_size=100),
    title=st.text(min_size=1, max_size=50).filter(lambda x: x.isidentifier())
)
def test_workspace_roundtrip_to_dict_from_dict(bundle_id, directory_id, username, title):
    original = ws.Workspace(
        title,
        BundleId=bundle_id,
        DirectoryId=directory_id,
        UserName=username
    )
    ws_dict = original.to_dict()
    recreated = ws.Workspace.from_dict(title + '_new', ws_dict)
    assert recreated.BundleId == original.BundleId
```

**Failing input**: `bundle_id='0', directory_id='0', username='0', title='A'`

## Reproducing the Bug

```python
import troposphere.workspaces as ws

workspace = ws.Workspace(
    'MyWorkspace',
    BundleId='bundle-123',
    DirectoryId='dir-456',
    UserName='testuser'
)

ws_dict = workspace.to_dict()
print(f"to_dict() output: {ws_dict}")

recreated = ws.Workspace.from_dict('RecreatedWorkspace', ws_dict)
```

## Why This Is A Bug

This violates the expected round-trip property that serialization and deserialization should be inverse operations. The `to_dict()` method produces `{'Properties': {...}, 'Type': '...'}` format (CloudFormation template format), but `from_dict()` expects just the properties dictionary without the wrapper. This inconsistency breaks the natural expectation that these methods should work together.

## Fix

The issue is that `to_dict()` returns CloudFormation template format while `from_dict()` expects raw properties. Either:
1. Make `from_dict()` accept the CloudFormation format by checking for and extracting the 'Properties' key
2. Add a separate method for CloudFormation serialization and make `to_dict()`/`from_dict()` consistent

```diff
# Option 1: Make from_dict handle CloudFormation format
@classmethod
def from_dict(cls, title, d):
+   # Handle CloudFormation template format  
+   if 'Properties' in d and 'Type' in d:
+       d = d['Properties']
    return cls._from_dict(title, **d)
```