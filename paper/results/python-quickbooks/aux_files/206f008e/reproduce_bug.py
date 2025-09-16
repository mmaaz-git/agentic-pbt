#!/usr/bin/env python3
"""Minimal reproduction of the error code 0 bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/python-quickbooks_env/lib/python3.13/site-packages')

from quickbooks import client, exceptions

# Test with error code 0
error_data = {
    "Fault": {
        "Error": [{
            "Message": "Test error",
            "code": "0",
            "Detail": "Test detail"
        }]
    }
}

try:
    client.QuickBooks.handle_exceptions(error_data["Fault"])
    print("No exception raised for error code 0")
except exceptions.AuthorizationException as e:
    print(f"AuthorizationException raised: {e}")
except exceptions.QuickbooksException as e:
    print(f"QuickbooksException raised: {e}")
    print(f"Error code: {e.error_code}")
    print(f"Expected: No exception or AuthorizationException (codes 1-499)")
    print("BUG: Error code 0 raises QuickbooksException instead of being handled correctly")