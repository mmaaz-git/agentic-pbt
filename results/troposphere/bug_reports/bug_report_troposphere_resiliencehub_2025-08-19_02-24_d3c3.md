# Bug Report: troposphere.resiliencehub Round-trip Serialization Failure

**Target**: `troposphere.resiliencehub.ResiliencyPolicy`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-19

## Summary

ResiliencyPolicy.from_dict() cannot deserialize the output of ResiliencyPolicy.to_dict() when the Policy contains FailurePolicy objects, violating the expected round-trip property for serialization/deserialization.

## Property-Based Test

```python
@given(
    title=st.text(min_size=1, max_size=50).filter(lambda x: x.isalnum()),
    name=st.text(min_size=1),
    tier=st.sampled_from(["MissionCritical", "Critical", "Important", "CoreServices", "NonCritical"]),
    policy_dict=st.dictionaries(
        keys=st.sampled_from(["Software", "Hardware", "AZ", "Region"]),
        values=st.builds(rh.FailurePolicy,
                        RpoInSecs=st.integers(min_value=0, max_value=86400),
                        RtoInSecs=st.integers(min_value=0, max_value=86400)),
        min_size=1
    )
)
def test_resiliency_policy_roundtrip(title, name, tier, policy_dict):
    """Property: ResiliencyPolicy to_dict should produce valid reconstruction data"""
    rp = rh.ResiliencyPolicy(
        title,
        PolicyName=name,
        Tier=tier,
        Policy=policy_dict
    )
    
    result = rp.to_dict()
    props = result["Properties"]
    
    # This fails - cannot reconstruct from serialized form
    rp2 = rh.ResiliencyPolicy.from_dict("TestPolicy2", props)
```

**Failing input**: `title='0', name='0', tier='MissionCritical', policy_dict={'Software': FailurePolicy(RpoInSecs=0, RtoInSecs=0)}`

## Reproducing the Bug

```python
import troposphere.resiliencehub as rh

failure_policy = rh.FailurePolicy(RpoInSecs=60, RtoInSecs=120)
policy = rh.ResiliencyPolicy(
    'TestPolicy',
    PolicyName='MyPolicy',
    Tier='Critical',
    Policy={'Software': failure_policy}
)

serialized = policy.to_dict()

try:
    reconstructed = rh.ResiliencyPolicy.from_dict('NewPolicy', serialized['Properties'])
    print("Success")
except ValueError as e:
    print(f"Failed: {e}")
```

## Why This Is A Bug

The to_dict() method converts FailurePolicy objects to plain dictionaries during serialization, but from_dict() expects the Policy values to be FailurePolicy instances, not dictionaries. This breaks the fundamental expectation that `from_dict(to_dict(obj))` should reconstruct the original object. Users cannot reliably serialize and deserialize ResiliencyPolicy objects, which is essential for template manipulation and storage.

## Fix

The from_dict() method needs to reconstruct FailurePolicy objects from their dictionary representations before validation. Here's a potential fix to the validate_resiliencypolicy_policy function or the from_dict method:

```diff
# In troposphere/validators/resiliencehub.py or in the from_dict preprocessing
def validate_resiliencypolicy_policy(policy):
    """
    Validate Type for Policy
    Property: ResiliencyPolicy.Policy
    """
    from ..resiliencehub import FailurePolicy

    VALID_POLICY_KEYS = ("Software", "Hardware", "AZ", "Region")

    if not isinstance(policy, dict):
        raise ValueError("Policy must be a dict")

    for k, v in policy.items():
        if k not in VALID_POLICY_KEYS:
            policy_keys = ", ".join(VALID_POLICY_KEYS)
            raise ValueError(f"Policy key must be one of {policy_keys}")

-       if not isinstance(v, FailurePolicy):
-           raise ValueError("Policy value must be FailurePolicy")
+       if not isinstance(v, FailurePolicy):
+           # Try to reconstruct FailurePolicy from dict (for from_dict compatibility)
+           if isinstance(v, dict) and 'RpoInSecs' in v and 'RtoInSecs' in v:
+               policy[k] = FailurePolicy(**v)
+           else:
+               raise ValueError("Policy value must be FailurePolicy or dict with RpoInSecs/RtoInSecs")

    return policy
```