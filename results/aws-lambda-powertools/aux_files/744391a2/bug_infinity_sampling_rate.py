#!/usr/bin/env python3
"""
Bug reproduction: 'Infinity' accepted as sampling rate without proper validation
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/aws-lambda-powertools_env/lib/python3.13/site-packages')

from aws_lambda_powertools.logging import Logger
from aws_lambda_powertools.logging.exceptions import InvalidLoggerSamplingRateError
from unittest.mock import patch

print("Bug: 'Infinity' string accepted as sampling rate")
print("="*60)
print()

# Test various special float values
special_values = ['Infinity', 'inf', '-Infinity', '-inf', 'NaN', 'nan']

for value in special_values:
    try:
        with patch('random.random', return_value=0.5):
            logger = Logger(service="test", sampling_rate=value)
            logger._configure_sampling()
            float_val = float(value)
            print(f"✗ '{value}' accepted! Converts to float({value}) = {float_val}")
            
            # Check if it's in valid range
            if 0.0 <= float_val <= 1.0:
                print(f"  Within [0,1] range: Yes")
            else:
                print(f"  Within [0,1] range: No - THIS IS A BUG!")
                
    except (ValueError, InvalidLoggerSamplingRateError) as e:
        print(f"✓ '{value}' properly rejected with: {type(e).__name__}")

print()
print("Expected behavior:")
print("- Only numeric values between 0.0 and 1.0 should be accepted")
print("- 'Infinity', 'NaN' etc. should raise InvalidLoggerSamplingRateError")
print()
print("Actual behavior:")
print("- 'Infinity', 'inf', 'NaN' etc. are accepted without validation")
print("- This violates the documented constraint of 0.0 to 1.0 range")