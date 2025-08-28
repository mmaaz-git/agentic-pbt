# Bug Report: troposphere Title Validation Rejects Valid CloudFormation Names

**Target**: `troposphere.systemsmanagersap.Application`, `troposphere.systemsmanagersap.Credential`, `troposphere.systemsmanagersap.ComponentInfo`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-19

## Summary

Title validation rejects underscores and other valid CloudFormation resource name characters, preventing common naming patterns used in AWS CloudFormation templates.

## Property-Based Test

```python
@given(
    cred_type=st.one_of(st.none(), credential_type_strategy),
    db_name=st.one_of(st.none(), aws_id_strategy),
    secret_id=st.one_of(st.none(), aws_id_strategy)
)
def test_credential_roundtrip(cred_type, db_name, secret_id):
    """Test that Credential.from_dict(cred.to_dict()) preserves data"""
    kwargs = {}
    if cred_type is not None:
        kwargs['CredentialType'] = cred_type
    if db_name is not None:
        kwargs['DatabaseName'] = db_name
    if secret_id is not None:
        kwargs['SecretId'] = secret_id
    
    cred1 = sap.Credential(**kwargs)
    dict1 = cred1.to_dict()
    
    # This fails with title validation error
    cred2 = sap.Credential.from_dict('cred_title', dict1)
    dict2 = cred2.to_dict()
    
    assert dict1 == dict2
```

**Failing input**: Using title `'cred_title'` with any valid properties

## Reproducing the Bug

```python
import troposphere.systemsmanagersap as sap

# Underscores are rejected in resource names
app = sap.Application('My_App', ApplicationId='app-123', ApplicationType='SAP/HANA')
# ValueError: Name "My_App" not alphanumeric

# This affects from_dict as well
cred = sap.Credential.from_dict('cred_title', {'CredentialType': 'ADMIN'})
# ValueError: Name "cred_title" not alphanumeric
```

## Why This Is A Bug

CloudFormation logical resource names commonly use underscores for readability (e.g., `My_Database_Instance`). The overly restrictive validation pattern prevents users from using standard CloudFormation naming conventions when generating templates with troposphere.

## Fix

Update the validation regex to allow underscores and other valid CloudFormation characters:

```diff
- valid_names = re.compile(r'^[a-zA-Z0-9]+$')
+ valid_names = re.compile(r'^[a-zA-Z][a-zA-Z0-9_]*$')
```