# Bug Report: aws_lambda_powertools.event_handler Route Compilation Fails with Regex Special Characters

**Target**: `aws_lambda_powertools.event_handler.api_gateway.ApiGatewayResolver._compile_regex`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `_compile_regex` method fails to escape regex special characters in static route segments, causing routes containing characters like `?`, `$`, `()`, `[]` to fail pattern matching even against identical paths.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from aws_lambda_powertools.event_handler.api_gateway import ApiGatewayResolver

@given(special_chars=st.text(alphabet=".*+?[]{}()|\\^$", min_size=1, max_size=5))
def test_route_with_regex_special_chars(special_chars):
    resolver = ApiGatewayResolver()
    route = f"/test/{special_chars}/end"
    
    compiled = resolver._compile_regex(route)
    test_path = f"/test/{special_chars}/end"
    match = compiled.match(test_path)
    
    assert match is not None, f"Route {route} didn't match path {test_path}"
```

**Failing input**: `special_chars='?'`

## Reproducing the Bug

```python
from aws_lambda_powertools.event_handler.api_gateway import ApiGatewayResolver

resolver = ApiGatewayResolver()

route = "/test?/end"
compiled = resolver._compile_regex(route)
test_path = "/test?/end"
match = compiled.match(test_path)

if not match:
    print(f"BUG: Route '{route}' failed to match identical path '{test_path}'")
```

## Why This Is A Bug

Routes should match paths that are identical to their pattern. When a route contains regex special characters like `?` in its static segments, these should be treated as literal characters, not regex metacharacters. The current implementation fails to escape these characters, causing the compiled regex to interpret `?` as "zero or one of the preceding character" rather than a literal question mark.

## Fix

The fix requires escaping regex special characters in static route segments before compiling the regex pattern:

```diff
--- a/aws_lambda_powertools/event_handler/api_gateway.py
+++ b/aws_lambda_powertools/event_handler/api_gateway.py
@@ -2478,7 +2478,9 @@ class ApiGatewayResolver(BaseRouter, Generic[ResponseEventT]):
 
         NOTE: See #520 for context
         """
-        rule_regex: str = re.sub(_DYNAMIC_ROUTE_PATTERN, _NAMED_GROUP_BOUNDARY_PATTERN, rule)
+        # First escape special regex characters in the entire rule
+        escaped_rule = re.escape(rule)
+        # Then process dynamic route patterns (restoring them from escaped form)
+        rule_regex: str = re.sub(r'\\<(.*?)\\>', lambda m: f"(?P<{m.group(1)}>[\\w\\-._~()'!*:@,;=+&$%<> \\[\\]{{}}|^]+)", escaped_rule)
         return re.compile(base_regex.format(rule_regex))
```