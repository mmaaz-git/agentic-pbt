# Bug Report: aws_lambda_powertools.package_logger Lack of Idempotence

**Target**: `aws_lambda_powertools.package_logger.set_package_logger_handler`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `set_package_logger_handler` function is not idempotent - multiple calls accumulate NullHandlers instead of maintaining a single handler configuration.

## Property-Based Test

```python
@given(st.one_of(st.none(), st.just(sys.stdout), st.just(sys.stderr)))
def test_idempotence_without_debug(stream):
    """Test that calling set_package_logger_handler multiple times is idempotent when debug is disabled."""
    with mock.patch.dict(os.environ, {constants.POWERTOOLS_DEBUG_ENV: "0"}, clear=True):
        logger = logging.getLogger("aws_lambda_powertools")
        logger.handlers.clear()
        
        package_logger.set_package_logger_handler(stream=stream)
        handlers_after_first = list(logger.handlers)
        
        package_logger.set_package_logger_handler(stream=stream)
        handlers_after_second = list(logger.handlers)
        
        assert len(handlers_after_first) == len(handlers_after_second)
```

**Failing input**: `stream=None`

## Reproducing the Bug

```python
import sys
import os
import logging

sys.path.insert(0, '/root/hypothesis-llm/envs/aws-lambda-powertools_env/lib/python3.13/site-packages')

import aws_lambda_powertools.package_logger as package_logger
from aws_lambda_powertools.shared import constants

os.environ[constants.POWERTOOLS_DEBUG_ENV] = "0"

logger = logging.getLogger("aws_lambda_powertools")
logger.handlers.clear()

package_logger.set_package_logger_handler()
print(f"After first call: {len(logger.handlers)} handlers")

package_logger.set_package_logger_handler()
print(f"After second call: {len(logger.handlers)} handlers")

package_logger.set_package_logger_handler()
print(f"After third call: {len(logger.handlers)} handlers")
```

## Why This Is A Bug

The function documentation states it "Sets up Powertools for AWS Lambda (Python) package logging," implying a configuration action that should be idempotent. Multiple calls accumulating handlers can lead to duplicate log output and unexpected behavior in applications that might call this initialization function multiple times.

## Fix

```diff
def set_package_logger_handler(stream=None):
    """Sets up Powertools for AWS Lambda (Python) package logging.

    By default, we discard any output to not interfere with customers logging.

    When POWERTOOLS_DEBUG env var is set, we setup `aws_lambda_powertools` logger in DEBUG level.

    Parameters
    ----------
    stream: sys.stdout
        log stream, stdout by default
    """

    if powertools_debug_is_set():
        return set_package_logger(stream=stream)

    logger = logging.getLogger("aws_lambda_powertools")
+   # Check if NullHandler already exists to ensure idempotence
+   if not any(isinstance(h, logging.NullHandler) for h in logger.handlers):
        logger.addHandler(logging.NullHandler())
    logger.propagate = False
```