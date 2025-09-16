# Bug Report: quickbooks.cdc Empty CDCResponse Causes IndexError

**Target**: `quickbooks.cdc.change_data_capture`
**Severity**: High
**Bug Type**: Crash
**Date**: 2025-08-18

## Summary

The `change_data_capture` function crashes with IndexError when the QuickBooks API returns an empty CDCResponse list, which can occur when there are no changes since the specified timestamp.

## Property-Based Test

```python
def test_empty_cdc_response_list_crashes():
    """Test that an empty CDCResponse list causes an IndexError"""
    qbo_classes = [MockQBOClass("Account")]
    
    mock_qb = Mock()
    mock_qb.change_data_capture = Mock(return_value={
        'CDCResponse': []  # Empty list!
    })
    
    with pytest.raises(IndexError):
        change_data_capture(qbo_classes, datetime.now(), qb=mock_qb)
```

**Failing input**: `{'CDCResponse': []}`

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
mock_qb.change_data_capture = Mock(return_value={'CDCResponse': []})

result = change_data_capture([MockQBOClass], datetime.now(), qb=mock_qb)
# Raises: IndexError: list index out of range
```

## Why This Is A Bug

The function assumes that `cdc_response_dict` always contains at least one element and directly accesses `cdc_response_dict[0]` on line 26 without checking if the list is empty. When the QuickBooks API returns no changes (empty CDCResponse), this causes an unhandled IndexError. This violates the expected behavior of gracefully handling API responses with no data.

## Fix

```diff
--- a/quickbooks/cdc.py
+++ b/quickbooks/cdc.py
@@ -20,11 +20,16 @@ def change_data_capture(qbo_class_list, timestamp, qb=None):
 
     resp = qb.change_data_capture(entity_list_string, timestamp_string)
 
     cdc_response_dict = resp.pop('CDCResponse')
     cdc_response = CDCResponse.from_json(resp)
 
+    # Handle empty CDCResponse
+    if not cdc_response_dict:
+        return cdc_response
+    
     query_response_list = cdc_response_dict[0]['QueryResponse']
     for query_response_dict in query_response_list:
         qb_object_names = [x for x in query_response_dict if x in cdc_class_names]
 
         if len(qb_object_names) == 1:
```