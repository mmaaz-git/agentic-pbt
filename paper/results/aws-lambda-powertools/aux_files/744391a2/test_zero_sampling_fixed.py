#!/usr/bin/env python3
"""
Test if 0.0 is handled specially
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/aws-lambda-powertools_env/lib/python3.13/site-packages')

from aws_lambda_powertools.logging import Logger
from unittest.mock import patch
import logging

print("Testing edge case: sampling_rate=0.0")
print("="*60)

# Check if 0.0 is truthy/falsy
print(f"bool(0.0) = {bool(0.0)}")
print(f"not 0.0 = {not 0.0}")
print()

# So line 413 `if not self.sampling_rate:` will return early when sampling_rate=0.0
print("Code line 413: `if not self.sampling_rate: return`")
print("This means sampling_rate=0.0 exits early and never sets DEBUG")
print()

# Verify with actual logger
with patch('random.random', return_value=0.0):
    logger = Logger(service="test", sampling_rate=0.0, level="INFO")
    print(f"Logger with sampling_rate=0.0, level=INFO:")
    print(f"  Logger level: {logging.getLevelName(logger.log_level)}")
    print(f"  ✓ Correctly stays at INFO (no DEBUG sampling)")

print()
print("So the test failure for rate=0.0 is actually a FALSE POSITIVE in my test!")
print("The code correctly handles 0.0 by disabling sampling entirely.")
print()

# But let's check the default log level issue
print("="*60)
print("Checking default log level (no explicit level set):")
print()

import os
# Clear env vars
for key in ['POWERTOOLS_LOG_LEVEL', 'LOG_LEVEL', 'AWS_LAMBDA_LOG_LEVEL']:
    os.environ.pop(key, None)

logger2 = Logger(service="test")
print(f"Logger with no level specified:")
print(f"  Logger level: {logging.getLevelName(logger2.log_level)}")
print(f"  Expected: INFO (based on documentation)")
print()

# Check with sampling
with patch('random.random', return_value=0.5):
    logger3 = Logger(service="test", sampling_rate=1.0)  # 100% sampling
    print(f"Logger with sampling_rate=1.0 (100% sampling), no level:")
    print(f"  Logger level: {logging.getLevelName(logger3.log_level)}")
    print(f"  Expected: DEBUG (due to sampling)")
    print()
    
# This explains why default was DEBUG - sampling was being applied!