# Bug Report: aws_lambda_powertools.package_logger Invalid Debug Values Crash

**Target**: `aws_lambda_powertools.package_logger.set_package_logger_handler`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `set_package_logger_handler` function crashes with ValueError when POWERTOOLS_DEBUG environment variable contains invalid boolean values instead of treating them as False.

## Property-Based Test

```python
@given(st.text(min_size=1).filter(lambda x: x.lower() not in ["true", "1", "y", "yes", "t", "on", "false", "0", "n", "no", "f", "off"]))
def test_invalid_debug_values_behavior(debug_value):
    """Test behavior with invalid debug values - should treat as disabled."""
    assume(debug_value.strip())
    
    with mock.patch.dict(os.environ, {constants.POWERTOOLS_DEBUG_ENV: debug_value}, clear=True):
        logger = logging.getLogger("aws_lambda_powertools")
        logger.handlers.clear()
        
        package_logger.set_package_logger_handler()
        
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], logging.NullHandler)
        assert logger.propagate == False
```

**Failing input**: `debug_value='2'` (or any non-boolean string like 'invalid', 'maybe', 'null', etc.)

## Reproducing the Bug

```python
import sys
import os

sys.path.insert(0, '/root/hypothesis-llm/envs/aws-lambda-powertools_env/lib/python3.13/site-packages')

import aws_lambda_powertools.package_logger as package_logger
from aws_lambda_powertools.shared import constants

invalid_values = ["2", "invalid", "maybe", "null"]

for value in invalid_values:
    print(f"Testing with POWERTOOLS_DEBUG='{value}'")
    os.environ[constants.POWERTOOLS_DEBUG_ENV] = value
    
    try:
        package_logger.set_package_logger_handler()
        print(f"  Handled gracefully")
    except ValueError as e:
        print(f"  CRASH: {e}")
```

## Why This Is A Bug

Environment variables can contain arbitrary values set by users or systems. The function should handle invalid values gracefully by treating them as False/disabled rather than crashing. This crash can prevent applications from starting if the environment variable is misconfigured.

## Fix

```diff
def powertools_debug_is_set() -> bool:
-    is_on = strtobool(os.getenv(constants.POWERTOOLS_DEBUG_ENV, "0"))
+    try:
+        is_on = strtobool(os.getenv(constants.POWERTOOLS_DEBUG_ENV, "0"))
+    except ValueError:
+        # Treat invalid values as False
+        return False
     if is_on:
         warnings.warn("POWERTOOLS_DEBUG environment variable is enabled. Setting logging level to DEBUG.", stacklevel=2)
         return True
 
     return False
```