# Bug Report: troposphere.sns Boolean String Case Sensitivity Inconsistency

**Target**: `troposphere.sns`
**Severity**: Low
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The boolean validator in troposphere accepts 'true'/'false' and 'True'/'False' but rejects 'TRUE'/'FALSE', creating an inconsistent case sensitivity behavior for string-to-boolean conversion.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.sns as sns

@given(st.sampled_from(['true', 'false']))
def test_boolean_case_consistency(base_value):
    topic = sns.Topic('TestTopic')
    
    # Test all case variants
    lowercase = base_value.lower()  # 'true' or 'false'
    titlecase = base_value.title()  # 'True' or 'False'  
    uppercase = base_value.upper()  # 'TRUE' or 'FALSE'
    
    # All should either work or all should fail for consistency
    results = []
    for variant in [lowercase, titlecase, uppercase]:
        try:
            topic.FifoTopic = variant
            results.append((variant, topic.properties.get('FifoTopic')))
        except:
            results.append((variant, None))
    
    # Check consistency
    working = [r for r in results if r[1] is not None]
    if working:
        # If any work, all should work with same result
        assert len(working) == 3, f"Inconsistent case handling: {results}"
```

**Failing input**: `'true'` leads to inconsistent behavior where 'true' and 'True' work but 'TRUE' fails

## Reproducing the Bug

```python
import troposphere.sns as sns

topic = sns.Topic('TestTopic')

topic.FifoTopic = 'true'
print(f"'true' -> {topic.properties.get('FifoTopic')}")

topic.FifoTopic = 'True'  
print(f"'True' -> {topic.properties.get('FifoTopic')}")

try:
    topic.FifoTopic = 'TRUE'
    print(f"'TRUE' -> {topic.properties.get('FifoTopic')}")
except:
    print("'TRUE' -> Rejected (ERROR)")

topic.FifoTopic = 'false'
print(f"'false' -> {topic.properties.get('FifoTopic')}")

topic.FifoTopic = 'False'
print(f"'False' -> {topic.properties.get('FifoTopic')}")

try:
    topic.FifoTopic = 'FALSE'
    print(f"'FALSE' -> {topic.properties.get('FifoTopic')}")
except:
    print("'FALSE' -> Rejected (ERROR)")
```

## Why This Is A Bug

The boolean validator's case sensitivity is inconsistent. It accepts both lowercase ('true'/'false') and title case ('True'/'False') but rejects uppercase ('TRUE'/'FALSE'). This violates the principle of least surprise - if the validator is case-insensitive enough to accept 'True', users would reasonably expect it to also accept 'TRUE'. The current behavior creates an arbitrary distinction between title case and uppercase that serves no clear purpose and could confuse users.

## Fix

The boolean validator should either be fully case-sensitive (only accepting exact matches) or fully case-insensitive (accepting all case variants). The fix would be to update the boolean validator function to handle all case variants consistently:

```diff
def boolean(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
-       if value in ['true', 'false', 'True', 'False', '0', '1']:
+       if value.lower() in ['true', 'false'] or value in ['0', '1']:
            return value.lower() == 'true' or value == '1'
    raise ValueError
```