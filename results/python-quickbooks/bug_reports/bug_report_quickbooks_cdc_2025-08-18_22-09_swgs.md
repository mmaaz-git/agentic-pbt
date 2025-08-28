# Bug Report: quickbooks.cdc Missing QueryResponse Key Causes KeyError

**Target**: `quickbooks.cdc.change_data_capture`
**Severity**: High
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `change_data_capture` function crashes with KeyError when the CDCResponse doesn't contain a 'QueryResponse' key, which can occur with malformed or unexpected API responses.

## Property-Based Test

```python
def test_missing_query_response_key_crashes():
    """Test that missing 'QueryResponse' key causes a KeyError"""
    qbo_classes = [MockQBOClass("Account")]
    
    mock_qb = Mock()
    mock_qb.change_data_capture = Mock(return_value={
        'CDCResponse': [{
            'SomeOtherKey': 'value'  # Missing 'QueryResponse' key!
        }]
    })
    
    with pytest.raises(KeyError):
        change_data_capture(qbo_classes, datetime.now(), qb=mock_qb)
```

**Failing input**: `{'CDCResponse': [{'SomeOtherKey': 'value'}]}`

## Reproducing the Bug

```python
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/python-quickbooks_env/lib/python3.13/site-packages')

from datetime import datetime
from unittest.mock import Mock
from quickbooks.cdc import change_data_capture

class MockQBOClass:
    qbo_object_name = "Account"
    
    @classmethod
    def from_json(cls, data):
        return cls()

mock_qb = Mock()
mock_qb.change_data_capture = Mock(return_value={
    'CDCResponse': [{'SomeOtherKey': 'value'}]
})

result = change_data_capture([MockQBOClass], datetime.now(), qb=mock_qb)
# Raises: KeyError: 'QueryResponse'
```

## Why This Is A Bug

The function assumes that every element in `cdc_response_dict` contains a 'QueryResponse' key and directly accesses it on line 26 without checking if the key exists. This causes an unhandled KeyError when the API returns a response with different structure or when there's an error response. The function should handle missing keys gracefully.

## Fix

```diff
--- a/quickbooks/cdc.py
+++ b/quickbooks/cdc.py
@@ -20,11 +20,17 @@ def change_data_capture(qbo_class_list, timestamp, qb=None):
 
     resp = qb.change_data_capture(entity_list_string, timestamp_string)
 
     cdc_response_dict = resp.pop('CDCResponse')
     cdc_response = CDCResponse.from_json(resp)
 
+    if not cdc_response_dict:
+        return cdc_response
+    
+    if 'QueryResponse' not in cdc_response_dict[0]:
+        return cdc_response
+    
     query_response_list = cdc_response_dict[0]['QueryResponse']
     for query_response_dict in query_response_list:
         qb_object_names = [x for x in query_response_dict if x in cdc_class_names]
 
         if len(qb_object_names) == 1:
```