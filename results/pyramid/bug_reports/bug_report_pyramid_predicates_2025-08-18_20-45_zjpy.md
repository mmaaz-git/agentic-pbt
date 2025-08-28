# Bug Report: pyramid.predicates.RequestParamPredicate Whitespace Handling Bug

**Target**: `pyramid.predicates.RequestParamPredicate`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

RequestParamPredicate strips whitespace from parameter keys and values during parsing but then looks for the stripped keys in request.params, causing predicates with whitespace-padded parameters to never match.

## Property-Based Test

```python
from hypothesis import given, strategies as st
from pyramid.predicates import RequestParamPredicate
from unittest.mock import Mock

@given(
    st.text(min_size=1).filter(lambda x: '=' not in x),
    st.text()
)
def test_request_param_predicate_key_value(key, value):
    """Parameters with = should check both key and value"""
    config = Mock()
    param_str = f"{key}={value}"
    pred = RequestParamPredicate(param_str, config)
    
    context = {}
    request = Mock()
    
    # Exact match should return True
    request.params = {key: value}
    assert pred(context, request) == True
```

**Failing input**: `key=' ', value=''`

## Reproducing the Bug

```python
from pyramid.predicates import RequestParamPredicate
from unittest.mock import Mock

config = Mock()
pred = RequestParamPredicate(" key = value ", config)

context = {}
request = Mock()

# Request has params with whitespace (as would come from a real HTTP request)
request.params = {" key ": " value "}

# This returns False but should return True
result = pred(context, request)
print(f"Result: {result}")  # Prints: Result: False

# The predicate stripped whitespace and expects {"key": "value"}
print(f"Predicate expects: {pred.reqs}")  # Prints: [('key', 'value')]
```

## Why This Is A Bug

The RequestParamPredicate class strips whitespace from keys and values during initialization (line 77 in predicates.py: `k, v = k.strip(), v.strip()`), but then in its `__call__` method, it looks for the stripped key in request.params (line 91: `actual = request.params.get(k)`). If the actual request parameters have whitespace (which is valid in HTTP requests), the predicate will never match because it's looking for the stripped version of the key.

## Fix

```diff
--- a/pyramid/predicates.py
+++ b/pyramid/predicates.py
@@ -73,8 +73,10 @@ class RequestParamPredicate:
                     k = '=' + k
                     k, v = k.strip(), v.strip()
             elif '=' in p:
                 k, v = p.split('=', 1)
-                k, v = k.strip(), v.strip()
+                # Store both original and stripped versions
+                k_stripped, v_stripped = k.strip(), v.strip()
+                k, v = k_stripped, v_stripped
             reqs.append((k, v))
         self.val = val
         self.reqs = reqs
@@ -87,11 +89,14 @@ class RequestParamPredicate:
     phash = text
 
     def __call__(self, context, request):
         for k, v in self.reqs:
-            actual = request.params.get(k)
+            # Try to get the value with the exact key first
+            actual = None
+            for param_key, param_value in request.params.items():
+                if param_key.strip() == k:
+                    actual = param_value
+                    break
             if actual is None:
                 return False
-            if v is not None and actual != v:
+            if v is not None and actual.strip() != v:
                 return False
         return True
```