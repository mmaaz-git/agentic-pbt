"""Minimal reproduction of the integer validator float truncation bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere import validators

# Bug: integer() validator accepts non-integer floats
result = validators.integer(1.5)
print(f"BUG: validators.integer(1.5) returned {result}")
print("Expected: ValueError('1.5 is not a valid integer')")
print(f"Impact: This treats 1.5 as integer value 1 (via int(1.5) = {int(1.5)})")

# This affects network_port as well
port = validators.network_port(80.5)
print(f"\nBUG: validators.network_port(80.5) returned {port}")
print("Expected: ValueError since 80.5 is not a valid integer port number")