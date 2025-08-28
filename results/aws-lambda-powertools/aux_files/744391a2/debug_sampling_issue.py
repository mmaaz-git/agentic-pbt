#!/usr/bin/env python3
"""
Debug why sampling isn't setting DEBUG level
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/aws-lambda-powertools_env/lib/python3.13/site-packages')

from aws_lambda_powertools.logging import Logger
from unittest.mock import patch, Mock
import logging
import os

# Clear env vars
for key in list(os.environ.keys()):
    if 'LOG' in key or 'POWERTOOLS' in key or 'AWS_LAMBDA' in key:
        os.environ.pop(key, None)

print("Debugging sampling mechanism")
print("="*60)
print()

# Patch random and trace what happens
original_random = __import__('random')

call_count = 0
def traced_random():
    global call_count
    call_count += 1
    result = 0.5
    print(f"  random.random() called (#{call_count}): returning {result}")
    return result

with patch('random.random', traced_random):
    print("Creating Logger with sampling_rate=0.8:")
    logger = Logger(service="test", sampling_rate=0.8)
    print(f"  Initial log level: {logging.getLevelName(logger.log_level)}")
    print(f"  Sampling rate: {logger.sampling_rate}")
    print()
    
    # Manually call _configure_sampling to see what happens
    print("Manually calling _configure_sampling():")
    logger._configure_sampling()
    print(f"  Log level after configure: {logging.getLevelName(logger.log_level)}")
    print()

# Let's trace through the __init__ process
print("="*60)
print("Tracing through Logger initialization:")
print()

with patch('random.random', return_value=0.1):
    print("Creating Logger with sampling_rate=0.5, random()=0.1:")
    logger2 = Logger(service="test", sampling_rate=0.5)
    print(f"  0.1 <= 0.5 = {0.1 <= 0.5} (should trigger DEBUG)")
    print(f"  Final log level: {logging.getLevelName(logger2.log_level)}")
    
print()
print("Testing with environment variable:")
os.environ['POWERTOOLS_LOGGER_SAMPLE_RATE'] = '0.5'
with patch('random.random', return_value=0.1):
    logger3 = Logger(service="test")
    print(f"  POWERTOOLS_LOGGER_SAMPLE_RATE=0.5, random()=0.1")
    print(f"  Final log level: {logging.getLevelName(logger3.log_level)}")