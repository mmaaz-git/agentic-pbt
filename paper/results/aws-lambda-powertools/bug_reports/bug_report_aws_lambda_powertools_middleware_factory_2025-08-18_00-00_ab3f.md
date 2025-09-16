# Bug Report: aws_lambda_powertools.middleware_factory ModuleNotFoundError with trace_execution

**Target**: `aws_lambda_powertools.middleware_factory.lambda_handler_decorator`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `lambda_handler_decorator` crashes with `ModuleNotFoundError` when `trace_execution=True` is set and the optional `aws_xray_sdk` dependency is not installed.

## Property-Based Test

```python
from hypothesis import given, strategies as st
import pytest
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/aws-lambda-powertools_env/lib/python3.13/site-packages')

from aws_lambda_powertools.middleware_factory import lambda_handler_decorator

@given(
    trace_flag=st.just(True),
    event_data=st.dictionaries(st.text(min_size=1), st.text()),
    context_data=st.dictionaries(st.text(min_size=1), st.text())
)
def test_trace_execution_flag(trace_flag, event_data, context_data):
    @lambda_handler_decorator(trace_execution=trace_flag)
    def test_middleware(handler, event, context):
        return handler(event, context)
    
    @test_middleware
    def test_handler(event, context):
        return "success"
    
    result = test_handler(event_data, context_data)
    assert result == "success"
```

**Failing input**: `trace_flag=True, event_data={}, context_data={}`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/aws-lambda-powertools_env/lib/python3.13/site-packages')

from aws_lambda_powertools.middleware_factory import lambda_handler_decorator

@lambda_handler_decorator(trace_execution=True)
def simple_middleware(handler, event, context):
    return handler(event, context)

@simple_middleware
def lambda_handler(event, context):
    return {"statusCode": 200, "body": "Hello"}

result = lambda_handler({}, {})
```

## Why This Is A Bug

The middleware factory documentation shows `trace_execution=True` as a valid parameter and includes it in examples, but doesn't mention that `aws_xray_sdk` is required. When users enable tracing without having the X-Ray SDK installed, the code crashes instead of gracefully handling the missing dependency or documenting it as required.

## Fix

```diff
--- a/aws_lambda_powertools/tracing/tracer.py
+++ b/aws_lambda_powertools/tracing/tracer.py
@@ -842,7 +842,14 @@ class Tracer(BaseProvider):
     def _patch_xray_provider(self):
         # Due to Lazy Import, we need to activate `core` attrib via import
         # we also need to include `patch`, `patch_all` methods
         # to ensure patch calls are done via the provider
-        from aws_xray_sdk.core import xray_recorder  # type: ignore
+        try:
+            from aws_xray_sdk.core import xray_recorder  # type: ignore
+            import aws_xray_sdk.core
+        except ImportError as e:
+            raise ImportError(
+                "aws_xray_sdk is required for tracing. "
+                "Install it with: pip install aws-xray-sdk"
+            ) from e
 
         provider = xray_recorder
         provider.patch = aws_xray_sdk.core.patch
```