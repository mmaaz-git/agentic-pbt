# Bug Report: troposphere.connectcampaignsv2 Empty Title Validation Bypass

**Target**: `troposphere.connectcampaignsv2.Campaign` (applies to all `BaseAWSObject` subclasses)
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

Empty string titles bypass alphanumeric validation in AWS resource objects, allowing creation of resources with invalid names that violate CloudFormation requirements.

## Property-Based Test

```python
def test_campaign_title_validation():
    """Test that Campaign title must be alphanumeric."""
    # Valid titles
    valid_titles = ['Campaign1', 'TestCampaign', 'ABC123']
    for title in valid_titles:
        c = ccv2.Campaign(title)
        assert c.title == title
    
    # Invalid titles - empty string should fail but doesn't
    invalid_titles = ['Campaign-1', 'Test Campaign', 'Campaign!', '123_Campaign', '']
    for title in invalid_titles:
        with pytest.raises(ValueError, match="alphanumeric"):
            ccv2.Campaign(title)
```

**Failing input**: `''` (empty string)

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')
import troposphere.connectcampaignsv2 as ccv2

# Empty title should be rejected but isn't
campaign = ccv2.Campaign('')
print(f"Created Campaign with empty title: {repr(campaign.title)}")

# Can even be serialized
d = campaign.to_dict(validation=False)
print(f"Type: {d['Type']}")

# But validate_title would reject it if called
try:
    campaign.validate_title()
except ValueError as e:
    print(f"Direct validate_title() correctly raises: {e}")
```

## Why This Is A Bug

The validation logic is inconsistent. The `validate_title()` method correctly rejects empty strings with the regex pattern `^[a-zA-Z0-9]+$`, but this validation is bypassed in `BaseAWSObject.__init__()` due to the conditional check `if self.title:` which skips validation when title is falsy (empty string). CloudFormation resource names must be alphanumeric and cannot be empty.

## Fix

```diff
--- a/troposphere/__init__.py
+++ b/troposphere/__init__.py
@@ -180,8 +180,8 @@ class BaseAWSObject:
         ]
 
         # try to validate the title if its there
-        if self.title:
-            self.validate_title()
+        if self.title is not None:
+            self.validate_title()
 
         # Create the list of properties set on this object by the user
         self.properties = {}
```