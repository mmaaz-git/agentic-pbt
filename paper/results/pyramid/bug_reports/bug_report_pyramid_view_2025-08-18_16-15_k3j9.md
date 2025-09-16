# Bug Report: pyramid.view AppendSlashNotFoundViewFactory Fails on Control Characters in Query String

**Target**: `pyramid.view.AppendSlashNotFoundViewFactory`
**Severity**: Medium
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `AppendSlashNotFoundViewFactory` in pyramid.view crashes with a `ValueError` when redirecting URLs that have query strings containing control characters (newlines, carriage returns, etc.).

## Property-Based Test

```python
from hypothesis import given, strategies as st, assume
import pyramid.view as view
from pyramid.httpexceptions import HTTPTemporaryRedirect

@given(st.text(min_size=1), st.text())
def test_append_slash_preserves_query_string(path_segment, query_string):
    assume('/' not in path_segment)
    assume('\x00' not in query_string)
    
    class MockRoute:
        def match(self, path):
            return {'match': 'data'} if path.endswith('/') else None
    
    class MockMapper:
        def get_routes(self):
            return [MockRoute()]
    
    class MockRegistry:
        def queryUtility(self, interface):
            from pyramid.interfaces import IRoutesMapper
            if interface == IRoutesMapper:
                return MockMapper()
            return None
    
    class MockRequest:
        def __init__(self, path, qs):
            self.path_info = path
            self.path = path
            self.query_string = qs
            self.registry = MockRegistry()
    
    class MockContext:
        pass
    
    factory = view.AppendSlashNotFoundViewFactory()
    request = MockRequest('/' + path_segment, query_string)
    context = MockContext()
    
    result = factory(context, request)
    
    if isinstance(result, HTTPTemporaryRedirect):
        if query_string:
            assert result.location == '/' + path_segment + '/' + '?' + query_string
        else:
            assert result.location == '/' + path_segment + '/'
```

**Failing input**: `path_segment='0', query_string='\n'`

## Reproducing the Bug

```python
from pyramid.view import AppendSlashNotFoundViewFactory
from pyramid.httpexceptions import HTTPTemporaryRedirect
from pyramid.interfaces import IRoutesMapper

class MockRoute:
    def match(self, path):
        return {'match': 'data'} if path.endswith('/') else None

class MockMapper:
    def get_routes(self):
        return [MockRoute()]

class MockRegistry:
    def queryUtility(self, interface):
        if interface == IRoutesMapper:
            return MockMapper()
        return None

class MockRequest:
    def __init__(self, path, query_string):
        self.path_info = path
        self.path = path
        self.query_string = query_string
        self.registry = MockRegistry()

class MockContext:
    pass

factory = AppendSlashNotFoundViewFactory()
request = MockRequest('/test', '\n')
context = MockContext()

result = factory(context, request)
```

## Why This Is A Bug

The `AppendSlashNotFoundViewFactory` is responsible for redirecting URLs without trailing slashes to their slash-appended equivalents when a matching route exists. However, it fails to sanitize query strings before using them in HTTP Location headers. This violates the HTTP specification which prohibits control characters in header values, causing the underlying WebOb library to raise a `ValueError`. This could affect real users who have malformed or malicious query strings in their URLs.

## Fix

```diff
--- a/pyramid/view.py
+++ b/pyramid/view.py
@@ -332,8 +332,12 @@ class AppendSlashNotFoundViewFactory:
                 if route.match(slashpath) is not None:
                     qs = request.query_string
                     if qs:
-                        qs = '?' + qs
-                    return self.redirect_class(
-                        location=request.path + '/' + qs
-                    )
+                        # Sanitize query string by removing control characters
+                        import re
+                        qs = re.sub(r'[\r\n]', '', qs)
+                        if qs:
+                            qs = '?' + qs
+                    location = request.path + '/' + (qs if qs else '')
+                    return self.redirect_class(location=location)
         return self.notfound_view(context, request)
```