# Bug Report: QuickBooks Error Code 0 Handling

**Target**: `quickbooks.client.QuickBooks.handle_exceptions`
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

The `handle_exceptions` method incorrectly handles error code 0, raising a generic `QuickbooksException` instead of following the documented error code classification scheme.

## Property-Based Test

```python
@given(error_code=st.integers(min_value=-10000, max_value=20000))
def test_handle_exceptions_error_code_mapping(error_code):
    """Test that error codes are mapped to the correct exception types as documented."""
    error_data = {
        "Fault": {
            "Error": [{
                "Message": "Test error",
                "code": str(error_code),
                "Detail": "Test detail"
            }]
        }
    }
    
    try:
        client.QuickBooks.handle_exceptions(error_data["Fault"])
        assert error_code <= 0
    except exceptions.AuthorizationException:
        assert 0 < error_code <= 499
    except exceptions.UnsupportedException:
        assert 500 <= error_code <= 599
    except exceptions.ObjectNotFoundException:
        assert error_code == 610
    except exceptions.GeneralException:
        assert (600 <= error_code <= 1999) and error_code != 610
    except exceptions.ValidationException:
        assert 2000 <= error_code <= 4999
    except exceptions.SevereException:
        assert error_code >= 10000
    except exceptions.QuickbooksException:
        assert error_code < 0 or (error_code > 4999 and error_code < 10000)
```

**Failing input**: `error_code=0`

## Reproducing the Bug

```python
from quickbooks import client, exceptions

error_data = {
    "Fault": {
        "Error": [{
            "Message": "Test error",
            "code": "0",
            "Detail": "Test detail"
        }]
    }
}

client.QuickBooks.handle_exceptions(error_data["Fault"])
```

## Why This Is A Bug

The `handle_exceptions` method uses the condition `if 0 < code <= 499:` to check for authorization errors, which excludes error code 0. This causes error code 0 to fall through to the else clause and raise a generic `QuickbooksException`. According to the documented error code ranges in the comment, this is inconsistent behavior. Error code 0 should either:
1. Be treated as part of the authorization error range (0-499)
2. Have special handling as "no error"
3. Be explicitly documented as a special case

The current implementation creates an edge case that violates the principle of consistent error classification.

## Fix

```diff
--- a/quickbooks/client.py
+++ b/quickbooks/client.py
@@ -286,7 +286,7 @@ class QuickBooks(object):
             if "code" in error:
                 code = int(error["code"])
 
-            if 0 < code <= 499:
+            if 0 <= code <= 499:
                 raise exceptions.AuthorizationException(message, code, detail)
             elif 500 <= code <= 599:
                 raise exceptions.UnsupportedException(message, code, detail)
```