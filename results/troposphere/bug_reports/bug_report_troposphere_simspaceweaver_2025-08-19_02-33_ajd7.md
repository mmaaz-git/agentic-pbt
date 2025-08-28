# Bug Report: troposphere.simspaceweaver Round-Trip Property Violation

**Target**: `troposphere.simspaceweaver.Simulation`
**Severity**: High
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

The round-trip property `from_dict(to_dict(x)) = x` is violated for the Simulation class (and all AWSObject-derived classes). The to_dict() method produces a structure that from_dict() cannot consume.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.simspaceweaver as ssw

valid_name = st.text(
    alphabet=st.characters(blacklist_categories=["Cc", "Cs"]),
    min_size=1,
    max_size=255
).filter(lambda s: s.replace("-", "").replace("_", "").isalnum())

valid_arn = st.text(min_size=1).map(lambda s: f"arn:aws:iam::123456789012:role/{s}")

@given(
    title=valid_name,
    name=valid_name,
    role_arn=valid_arn
)
def test_simulation_round_trip(title, name, role_arn):
    original = ssw.Simulation(title, Name=name, RoleArn=role_arn)
    d = original.to_dict()
    restored = ssw.Simulation.from_dict("NewTitle", d)  # This fails
    assert restored.to_dict() == d
```

**Failing input**: Any valid input, e.g., `title='TestSim', name='MySimulation', role_arn='arn:aws:iam::123456789012:role/SimRole'`

## Reproducing the Bug

```python
import troposphere.simspaceweaver as ssw

sim = ssw.Simulation('TestSim', Name='MySimulation', RoleArn='arn:aws:iam::123456789012:role/SimRole')
d = sim.to_dict()
print(f"to_dict output: {d}")

sim2 = ssw.Simulation.from_dict('TestSim2', d)
```

## Why This Is A Bug

The to_dict() method outputs a dict with structure `{'Properties': {...}, 'Type': '...'}`, but from_dict() expects only the properties dict without the wrapper. This violates the expected round-trip property that serialization and deserialization should be inverse operations. This affects all AWSObject-derived classes in troposphere, not just simspaceweaver.

## Fix

The from_dict() method needs to handle the structure produced by to_dict():

```diff
@classmethod
def from_dict(cls, title, d):
+   # If the dict has the structure from to_dict(), extract Properties
+   if 'Properties' in d and 'Type' in d:
+       return cls._from_dict(title, **d['Properties'])
    return cls._from_dict(title, **d)
```

Alternatively, to_dict() could be modified to return only the properties for consistency with from_dict() expectations, but this would be a breaking change to the API.