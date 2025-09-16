# Bug Report: troposphere.voiceid Title Validation Too Restrictive

**Target**: `troposphere.voiceid.Domain`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

The `Domain` class (and other AWS resource classes) reject valid CloudFormation resource names that contain hyphens, underscores, colons, and other common characters, only accepting alphanumeric titles.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import troposphere.voiceid as voiceid

# Strategy for valid CloudFormation resource names
name_strategy = st.text(min_size=1, max_size=200).filter(lambda x: x.strip())

@given(
    title=name_strategy,
    name=name_strategy,
    kms_key_id=st.text(min_size=1, max_size=100)
)
def test_domain_creation_with_various_titles(title, name, kms_key_id):
    """Test that Domain accepts various title formats"""
    domain = voiceid.Domain(
        title,
        Name=name,
        ServerSideEncryptionConfiguration=voiceid.ServerSideEncryptionConfiguration(
            KmsKeyId=kms_key_id
        )
    )
    assert domain.title == title
```

**Failing input**: `title='{'` (also fails with `':'`, `'-'`, `'_'`, etc.)

## Reproducing the Bug

```python
import troposphere.voiceid as voiceid

# Common CloudFormation naming patterns that should work but don't
test_titles = [
    'My-VoiceID-Domain',      # Hyphens are common in CFN
    'My_VoiceID_Domain',      # Underscores are valid
    'AWS::VoiceID::Domain',   # Standard CFN resource type format
    'Domain.Production',      # Dots for namespacing
]

for title in test_titles:
    try:
        domain = voiceid.Domain(
            title,
            Name='TestDomain',
            ServerSideEncryptionConfiguration=voiceid.ServerSideEncryptionConfiguration(
                KmsKeyId='test-key'
            )
        )
        print(f"✓ '{title}' worked")
    except ValueError as e:
        print(f"✗ '{title}' failed: {e}")
```

## Why This Is A Bug

CloudFormation resource logical IDs support alphanumeric characters, hyphens, underscores, and other characters. The current validation pattern `^[a-zA-Z0-9]+$` is overly restrictive and prevents users from using standard CloudFormation naming conventions. This breaks compatibility with existing CloudFormation templates and common naming patterns.

## Fix

The validation regex should be updated to match CloudFormation's actual requirements for logical IDs:

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -70,7 +70,7 @@
 
 # Regex to match and replace special characters in 
 # an input value specified in the Name parameter
-valid_names = re.compile(r"^[a-zA-Z0-9]+$")
+valid_names = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9\-_.:]*$")
 
 
 def encode_to_dict(obj):
```