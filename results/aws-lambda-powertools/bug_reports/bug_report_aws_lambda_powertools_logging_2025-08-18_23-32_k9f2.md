# Bug Report: aws_lambda_powertools.logging Invalid Sampling Rate Validation

**Target**: `aws_lambda_powertools.logging.Logger`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

Logger accepts invalid sampling rates like 'Infinity', 'NaN', and negative infinity that violate the documented 0.0-1.0 range constraint.

## Property-Based Test

```python
from hypothesis import given, strategies as st, settings
from aws_lambda_powertools.logging import Logger
from aws_lambda_powertools.logging.exceptions import InvalidLoggerSamplingRateError
from unittest.mock import patch
import pytest

invalid_special_floats = st.sampled_from(['Infinity', 'inf', '-Infinity', '-inf', 'NaN', 'nan'])

@given(rate=invalid_special_floats)
@settings(max_examples=50)
def test_special_float_rejection(rate):
    """Property: Special float values should raise InvalidLoggerSamplingRateError."""
    with patch('random.random', return_value=0.5):
        logger = Logger(service="test", sampling_rate=rate)
        with pytest.raises(InvalidLoggerSamplingRateError):
            logger._configure_sampling()
```

**Failing input**: `'Infinity'`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/aws-lambda-powertools_env/lib/python3.13/site-packages')

from aws_lambda_powertools.logging import Logger
from unittest.mock import patch

with patch('random.random', return_value=0.5):
    logger = Logger(service="test", sampling_rate='Infinity')
    logger._configure_sampling()
    print(f"Sampling rate: {logger.sampling_rate}")
    print(f"float('Infinity') = {float('Infinity')}")
    print(f"Is inf in range [0,1]? {0.0 <= float('Infinity') <= 1.0}")
```

## Why This Is A Bug

The Logger documentation and error message explicitly state that sampling_rate must be "a float value ranging 0 to 1". The values 'Infinity', '-Infinity', and 'NaN' convert to valid Python floats but fall outside the [0.0, 1.0] range. The code only validates that the value can be converted to float, not that it's within the valid range.

## Fix

```diff
--- a/aws_lambda_powertools/logging/logger.py
+++ b/aws_lambda_powertools/logging/logger.py
@@ -1,4 +1,5 @@
 import random
+import math
 
 def _configure_sampling(self) -> None:
     """Dynamically set log level based on sampling rate
@@ -414,11 +415,17 @@ def _configure_sampling(self) -> None:
         return
 
     try:
-        # This is not testing < 0 or > 1 conditions
-        # Because I don't need other if condition here
-        if random.random() <= float(self.sampling_rate):
+        sampling_rate_float = float(self.sampling_rate)
+        
+        # Validate that the sampling rate is within valid range and not special values
+        if not (0.0 <= sampling_rate_float <= 1.0) or math.isnan(sampling_rate_float) or math.isinf(sampling_rate_float):
+            raise ValueError("Sampling rate must be between 0.0 and 1.0")
+        
+        if random.random() <= sampling_rate_float:
             self._logger.setLevel(logging.DEBUG)
             logger.debug("Setting log level to DEBUG due to sampling rate")
     except ValueError:
         raise InvalidLoggerSamplingRateError(
             (
                 f"Expected a float value ranging 0 to 1, but received {self.sampling_rate} instead."
```