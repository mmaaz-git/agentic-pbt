# Bug Report: pyramid.renderers JSONP Callback Validation Overly Restrictive

**Target**: `pyramid.renderers.JSONP`
**Severity**: Medium
**Bug Type**: Contract
**Date**: 2025-08-18

## Summary

The JSONP renderer's callback validation regex incorrectly requires a minimum of 3 characters, rejecting common valid JavaScript callback names like 'cb', 'fn', and single-character identifiers.

## Property-Based Test

```python
def test_jsonp_callback_validation_too_restrictive():
    """Test that shows JSONP callback validation is overly restrictive."""
    pattern = renderers.JSONP_VALID_CALLBACK
    
    # These are all valid JavaScript identifiers that should work as callbacks
    # but are rejected by the current regex
    common_short_callbacks = [
        'cb',  # Very common abbreviation for callback
        'fn',  # Common abbreviation for function  
        'f',   # Single letter callbacks are valid JS
        '_',   # Valid JS identifier
        '$',   # jQuery-style, valid JS identifier
        'x0',  # Two chars starting with letter
        '_a',  # Two chars starting with underscore
        '$0',  # Two chars starting with $
    ]
    
    rejections = []
    for callback in common_short_callbacks:
        if not pattern.match(callback):
            rejections.append(callback)
    
    # All these valid JS identifiers are rejected
    assert rejections == common_short_callbacks
```

**Failing input**: Any callback name with fewer than 3 characters

## Reproducing the Bug

```python
from pyramid.renderers import JSONP
from pyramid.httpexceptions import HTTPBadRequest

jsonp_renderer = JSONP()

class MockInfo:
    pass

class MockRequest:
    def __init__(self, callback):
        self.GET = {'callback': callback}
        self.response = type('MockResponse', (), {
            'default_content_type': 'text/html',
            'content_type': 'text/html'
        })()

render_func = jsonp_renderer(MockInfo())

# This will raise HTTPBadRequest but shouldn't
request = MockRequest('cb')
system = {'request': request}
try:
    result = render_func({"data": "test"}, system)
except HTTPBadRequest:
    print("ERROR: Valid callback 'cb' was rejected")
```

## Why This Is A Bug

The regex pattern `^[$a-z_][$0-9a-z_\.\[\]]+[^.]$` requires:
1. One character from `[$a-z_]`
2. One or more characters from `[$0-9a-z_\.\[\]]` 
3. One character that's not a dot

This enforces a minimum of 3 characters, but valid JavaScript identifiers can be as short as 1 character. Common callback names like 'cb', 'fn', '_', and '$' are legitimate JavaScript identifiers that should be accepted for JSONP callbacks but are incorrectly rejected.

## Fix

```diff
--- a/pyramid/renderers.py
+++ b/pyramid/renderers.py
@@ -295,7 +295,7 @@ class JSON:
 
 json_renderer_factory = JSON()  # bw compat
 
-JSONP_VALID_CALLBACK = re.compile(r"^[$a-z_][$0-9a-z_\.\[\]]+[^.]$", re.I)
+JSONP_VALID_CALLBACK = re.compile(r"^[$a-z_][$0-9a-z_\.\[\]]*$(?<!\.)$", re.I)
 
 
 class JSONP(JSON):
```

Alternative fix that's more explicit:
```diff
--- a/pyramid/renderers.py
+++ b/pyramid/renderers.py
@@ -295,7 +295,9 @@ class JSON:
 
 json_renderer_factory = JSON()  # bw compat
 
-JSONP_VALID_CALLBACK = re.compile(r"^[$a-z_][$0-9a-z_\.\[\]]+[^.]$", re.I)
+# Allow valid JS identifiers: start with [$a-z_], continue with [$0-9a-z_.\[\]]*
+# Must not end with a dot
+JSONP_VALID_CALLBACK = re.compile(r"^[$a-z_]([$0-9a-z_\.\[\]]*[^.])?$", re.I)
 
 
 class JSONP(JSON):
```