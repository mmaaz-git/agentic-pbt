# Bug Report: troposphere.awslambda Environment Variable Name Validation Accepts Invalid Characters

**Target**: `troposphere.validators.awslambda.validate_variables_name`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-01-18

## Summary

The environment variable name validation in troposphere.awslambda incorrectly accepts variable names containing invalid characters (colons, hyphens, dots, spaces, etc.) after a valid prefix, which would cause AWS deployment failures.

## Property-Based Test

```python
@given(st.dictionaries(st.text(), st.text()))
def test_environment_variables_validation(variables):
    """Test environment variable name validation rules."""
    from troposphere.validators.awslambda import validate_variables_name
    
    RESERVED_ENVIRONMENT_VARIABLES = [
        "AWS_ACCESS_KEY", "AWS_ACCESS_KEY_ID", "AWS_DEFAULT_REGION",
        "AWS_EXECUTION_ENV", "AWS_LAMBDA_FUNCTION_MEMORY_SIZE",
        "AWS_LAMBDA_FUNCTION_NAME", "AWS_LAMBDA_FUNCTION_VERSION",
        "AWS_LAMBDA_LOG_GROUP_NAME", "AWS_LAMBDA_LOG_STREAM_NAME",
        "AWS_REGION", "AWS_SECRET_ACCESS_KEY", "AWS_SECRET_KEY",
        "AWS_SECURITY_TOKEN", "AWS_SESSION_TOKEN",
        "LAMBDA_RUNTIME_DIR", "LAMBDA_TASK_ROOT"
    ]
    ENVIRONMENT_VARIABLES_NAME_PATTERN = r"^[a-zA-Z][a-zA-Z0-9_]+$"
    
    should_fail = False
    for name in variables.keys():
        if name in RESERVED_ENVIRONMENT_VARIABLES:
            should_fail = True
            break
        if not re.match(ENVIRONMENT_VARIABLES_NAME_PATTERN, name):
            should_fail = True
            break
    
    if should_fail:
        try:
            validate_variables_name(variables)
            assert False, f"Expected ValueError for variables {variables}"
        except ValueError:
            pass
    else:
        result = validate_variables_name(variables)
        assert result == variables
```

**Failing input**: `{'A0:': ''}`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators.awslambda import validate_variables_name

# These should all fail but don't - they contain invalid characters
invalid_names = {
    "MY_VAR:PROD": "value1",    # Contains colon
    "API-KEY": "value2",         # Contains hyphen  
    "DB.HOST": "value3",         # Contains dot
    "USER@NAME": "value4",       # Contains @
    "PATH/TO/FILE": "value5"     # Contains slash
}

# This should raise ValueError but doesn't
result = validate_variables_name(invalid_names)
print(f"Accepted invalid names: {list(invalid_names.keys())}")

# Demonstration with a simple case
validate_variables_name({"A0:": "value"})  # Accepts 'A0:' which has invalid ':'
print("BUG: Accepted 'A0:' as valid environment variable name")
```

## Why This Is A Bug

AWS Lambda environment variable names must only contain letters, numbers, and underscores, and must start with a letter. The validation function is supposed to enforce this, but due to incorrect regex matching, it accepts names with invalid characters after a valid prefix. This causes CloudFormation templates to pass local validation but fail during AWS deployment with errors like "Environment variable name contains invalid characters".

## Fix

```diff
--- a/troposphere/validators/awslambda.py
+++ b/troposphere/validators/awslambda.py
@@ -78,7 +78,7 @@ def validate_variables_name(variables):
                 "Lambda Function environment variables names"
                 " can't be none of:\n %s" % ", ".join(RESERVED_ENVIRONMENT_VARIABLES)
             )
-        elif not re.match(ENVIRONMENT_VARIABLES_NAME_PATTERN, name):
+        elif not re.fullmatch(ENVIRONMENT_VARIABLES_NAME_PATTERN, name):
             raise ValueError("Invalid environment variable name: %s" % name)
 
     return variables
```