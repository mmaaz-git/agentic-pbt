#!/usr/bin/env python3
"""
Reproducing the 'Infinity' sampling rate bug
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/aws-lambda-powertools_env/lib/python3.13/site-packages')

from aws_lambda_powertools.logging import Logger
from unittest.mock import patch

# Test 1: 'Infinity' string is accepted as valid sampling rate
print("Test 1: 'Infinity' string handling")
print("="*50)

with patch('random.random', return_value=0.5):
    logger = Logger(service="test", sampling_rate='Infinity')
    logger._configure_sampling()
    print(f"Sampling rate set to: {logger.sampling_rate}")
    print(f"Logger level: {logger.log_level}")
    print("No exception raised! Bug confirmed.")
    print()

# Test what happens with float('Infinity')
print("Testing float('Infinity'):")
print("float('Infinity') =", float('Infinity'))
print("float('Infinity') <= 0.5 =", float('Infinity') <= 0.5)
print()

# Test 2: Rate = 0.0 issue
print("\nTest 2: Rate = 0.0 behavior")
print("="*50)

import random
random.seed(42)
with patch('random.random', return_value=0.5):
    logger = Logger(service="test", sampling_rate=0.0, level="INFO")
    print(f"Sampling rate: {logger.sampling_rate}")
    print(f"random.random() = 0.5")
    print(f"0.5 <= 0.0 = {0.5 <= 0.0}")
    print(f"Logger level: {logger.log_level}")
    print(f"Expected: INFO (20), Got: {logger.log_level}")
    
# Test with random value = 0.0
with patch('random.random', return_value=0.0):
    logger2 = Logger(service="test", sampling_rate=0.0, level="INFO")
    print(f"\nWith random.random() = 0.0:")
    print(f"0.0 <= 0.0 = {0.0 <= 0.0}")
    print(f"Logger level: {logger2.log_level}")
    print(f"Expected: INFO (20), Got: {logger2.log_level}")

# Test 3: Default log level when nothing is set
print("\nTest 3: Default log level")
print("="*50)

import os
# Clear all env vars
for key in list(os.environ.keys()):
    if 'LOG_LEVEL' in key or 'POWERTOOLS' in key or 'AWS_LAMBDA' in key:
        del os.environ[key]

logger3 = Logger(service="test")
print(f"Logger level when no level specified: {logger3.log_level}")
print(f"Expected: INFO (20), Got: {logger3.log_level}")