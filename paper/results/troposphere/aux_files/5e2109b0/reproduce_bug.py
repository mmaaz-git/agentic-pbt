"""Minimal reproduction of the tuple formatting bug in troposphere.wisdom.double"""

import troposphere.wisdom as wisdom

# Test with single-element tuple
input_value = (42,)

try:
    wisdom.double(input_value)
except ValueError as e:
    error_message = str(e)
    expected_message = f"{input_value!r} is not a valid double"
    
    print(f"Input: {input_value!r}")
    print(f"Actual error: {error_message!r}")
    print(f"Expected error: {expected_message!r}")
    print(f"BUG: Error message is incorrect!")
    
# The bug: '%r' formatting with a single-element tuple
# causes Python to unpack the tuple in the formatting operation