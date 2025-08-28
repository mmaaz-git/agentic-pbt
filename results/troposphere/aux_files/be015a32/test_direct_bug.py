#!/usr/bin/env python
"""Direct test to demonstrate the string formatting bug"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators.glue import connection_type_validator

# This should trigger the bug
try:
    result = connection_type_validator("INVALID_TYPE")
    print(f"Unexpectedly succeeded with result: {result}")
except ValueError as e:
    print(f"ValueError raised with message: {e}")
    # Check if the error message is malformed
    error_msg = str(e)
    if "%" in error_msg and "INVALID_TYPE" not in error_msg:
        print("BUG CONFIRMED: Error message has % instead of the actual invalid value")
        print(f"Expected: 'INVALID_TYPE is not a valid value for ConnectionType'")
        print(f"Got: '{error_msg}'")
    elif "INVALID_TYPE" in error_msg:
        print("Bug might be fixed or Python version handles it differently")
except TypeError as e:
    print(f"TypeError raised (formatting bug): {e}")
    print("BUG CONFIRMED: String formatting failed with TypeError")