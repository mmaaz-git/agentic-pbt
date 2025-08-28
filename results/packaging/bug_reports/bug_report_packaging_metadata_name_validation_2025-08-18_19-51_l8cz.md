# Bug Report: packaging.metadata Name Validation Inconsistency

**Target**: `packaging.metadata`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The `parse_email` function accepts package names that are later rejected by `Metadata.from_raw` and `Metadata.from_email`, violating the expected consistency between parsing methods.

## Property-Based Test

```python
from hypothesis import given
import packaging.metadata
from test_packaging_metadata import valid_metadata_email

@given(valid_metadata_email())
def test_parse_and_from_raw_consistency(data):
    raw_metadata, _ = packaging.metadata.parse_email(data)
    
    try:
        metadata1 = packaging.metadata.Metadata.from_raw(raw_metadata)
        metadata2 = packaging.metadata.Metadata.from_email(data)
        
        assert metadata1.name == metadata2.name
        assert metadata1.version == metadata2.version
    except packaging.metadata.InvalidMetadata:
        try:
            packaging.metadata.Metadata.from_email(data)
            assert False, "from_email should have failed if from_raw failed"
        except packaging.metadata.InvalidMetadata:
            pass
```

**Failing input**: `'Metadata-Version: 2.1\nName: A-\nVersion: 1.0.0'`

## Reproducing the Bug

```python
import packaging.metadata

metadata_str = '''Metadata-Version: 2.1
Name: A-
Version: 1.0.0'''

raw_metadata, unparsed = packaging.metadata.parse_email(metadata_str)
print(f"parse_email succeeded, name: {raw_metadata['name']}")

try:
    metadata = packaging.metadata.Metadata.from_raw(raw_metadata)
    print("from_raw succeeded")
except Exception as e:
    print(f"from_raw failed: {e}")

try:
    metadata = packaging.metadata.Metadata.from_email(metadata_str)
    print("from_email succeeded")
except Exception as e:
    print(f"from_email failed: {e}")
```

## Why This Is A Bug

The `parse_email` function successfully parses metadata with the package name "A-", but when this parsed data is passed to `Metadata.from_raw`, it fails validation. This breaks the expected contract that data successfully parsed by `parse_email` should be usable with `Metadata.from_raw`. The inconsistency means developers cannot reliably use `parse_email` to pre-validate metadata before creating `Metadata` objects.

## Fix

The issue is that `parse_email` doesn't validate package names according to PEP standards, while `Metadata.from_raw` does. Either:

1. `parse_email` should validate package names and reject invalid ones like "A-"
2. `Metadata.from_raw` should accept whatever `parse_email` produces
3. Document this behavior clearly as expected

The most consistent approach would be option 1 - validate names in `parse_email` to match the validation in `Metadata.from_raw`.