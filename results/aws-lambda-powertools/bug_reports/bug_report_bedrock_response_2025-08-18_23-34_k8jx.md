# Bug Report: BedrockResponse.is_json() Always Returns True

**Target**: `aws_lambda_powertools.event_handler.api_gateway.BedrockResponse.is_json`
**Severity**: Low
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `BedrockResponse.is_json()` method always returns `True` regardless of the actual content type, incorrectly reporting non-JSON content as JSON.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from aws_lambda_powertools.event_handler.api_gateway import BedrockResponse

@given(content_type=st.text(min_size=1, max_size=100))
def test_bedrock_response_is_json(content_type):
    response = BedrockResponse(body="test", content_type=content_type)
    result = response.is_json()
    
    if "json" not in content_type.lower():
        assert result == False, f"is_json() returned True for non-JSON content_type: {content_type}"
```

**Failing input**: `content_type='text/plain'`

## Reproducing the Bug

```python
from aws_lambda_powertools.event_handler.api_gateway import BedrockResponse

response = BedrockResponse(
    body="<html>Not JSON</html>",
    content_type="text/html"
)

print(f"Content-Type: {response.content_type}")
print(f"is_json(): {response.is_json()}")
```

## Why This Is A Bug

The `is_json()` method should return `True` only when the content type indicates JSON data (e.g., "application/json"). The current implementation hardcodes the return value to `True`, which misleads callers about the actual content type and could cause incorrect content handling downstream.

## Fix

```diff
--- a/aws_lambda_powertools/event_handler/api_gateway.py
+++ b/aws_lambda_powertools/event_handler/api_gateway.py
@@ -282,7 +282,7 @@ class BedrockResponse(Generic[ResponseT]):
     def is_json(self) -> bool:
         """
         Returns True if the response is JSON, based on the Content-Type.
         """
-        return True
+        return "json" in self.content_type.lower()
```