# Bug Report: troposphere.route53profiles from_dict Cannot Parse to_json Output

**Target**: `troposphere.route53profiles.Profile.from_dict`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `from_dict()` class method cannot parse the JSON structure produced by `to_json()`, violating the expected round-trip property between serialization and deserialization.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import json
import troposphere.route53profiles as r53p

valid_name = st.text(min_size=1, max_size=100).filter(lambda x: x.strip())

@given(name=valid_name)
def test_profile_json_roundtrip(name):
    profile = r53p.Profile('TestProfile', Name=name)
    json_str = profile.to_json()
    parsed = json.loads(json_str)
    recreated = r53p.Profile.from_dict('Recreated', parsed)
    assert recreated.to_json() == json_str
```

**Failing input**: `name='0'`

## Reproducing the Bug

```python
import json
import troposphere.route53profiles as r53p

profile = r53p.Profile('TestProfile', Name='TestName')
json_str = profile.to_json()
parsed = json.loads(json_str)

try:
    recreated = r53p.Profile.from_dict('Recreated', parsed)
except AttributeError as e:
    print(f"Error: {e}")
```

## Why This Is A Bug

The `to_json()` method produces a dict with structure `{"Properties": {...}, "Type": "..."}`, but `from_dict()` expects only the Properties dict directly. This breaks the natural expectation that `from_dict()` should be able to consume what `to_dict()`/`to_json()` produces, making round-trip serialization impossible without manual intervention.

## Fix

The `from_dict()` method should handle both formats - the full CloudFormation template structure and just the Properties dict:

```diff
@classmethod
def from_dict(cls, title, d):
+   # Handle full CloudFormation structure
+   if 'Properties' in d and 'Type' in d:
+       return cls._from_dict(title, **d['Properties'])
    return cls._from_dict(title, **d)
```