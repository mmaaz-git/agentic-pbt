# Bug Report: troposphere.qldb Round-Trip Property Violation

**Target**: `troposphere.qldb.Ledger` and `troposphere.qldb.Stream`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `to_dict()` and `from_dict()` methods in troposphere.qldb AWS objects are not inverses of each other, violating the expected round-trip property.

## Property-Based Test

```python
@given(
    deletion_protection=st.booleans(),
    kms_key=st.text(min_size=1, alphabet=st.characters(blacklist_categories=["Cc"])),
    name=st.text(min_size=1, alphabet=st.characters(blacklist_categories=["Cc"])),
    permissions_mode=st.sampled_from(["ALLOW_ALL", "STANDARD"])
)
def test_ledger_to_dict_from_dict_roundtrip(deletion_protection, kms_key, name, permissions_mode):
    ledger = qldb.Ledger(
        'TestLedger',
        DeletionProtection=deletion_protection,
        KmsKey=kms_key,
        Name=name,
        PermissionsMode=permissions_mode
    )
    
    dict_repr = ledger.to_dict()
    new_ledger = qldb.Ledger.from_dict('ReconstructedLedger', dict_repr)
    new_dict_repr = new_ledger.to_dict()
    
    assert dict_repr == new_dict_repr
```

**Failing input**: Any valid input fails (e.g., `deletion_protection=False, kms_key='0', name='0', permissions_mode='ALLOW_ALL'`)

## Reproducing the Bug

```python
import troposphere.qldb as qldb

ledger = qldb.Ledger('TestLedger', PermissionsMode='ALLOW_ALL')
dict_repr = ledger.to_dict()
print('to_dict() output:', dict_repr)

new_ledger = qldb.Ledger.from_dict('Reconstructed', dict_repr)
```

## Why This Is A Bug

The `to_dict()` method outputs a CloudFormation-style dictionary with 'Properties' and 'Type' keys:
```
{'Properties': {'PermissionsMode': 'ALLOW_ALL'}, 'Type': 'AWS::QLDB::Ledger'}
```

However, `from_dict()` expects only the properties dictionary directly, not the wrapped format. This breaks the fundamental round-trip property that `from_dict(to_dict(x))` should reconstruct the original object.

## Fix

The `from_dict()` method should handle the CloudFormation format output by `to_dict()`:

```diff
@classmethod
def from_dict(cls, title, d):
+   # Handle CloudFormation format with 'Properties' key
+   if 'Properties' in d and 'Type' in d:
+       return cls._from_dict(title, **d['Properties'])
    return cls._from_dict(title, **d)
```