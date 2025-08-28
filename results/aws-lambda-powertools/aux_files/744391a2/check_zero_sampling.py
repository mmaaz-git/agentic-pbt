#!/usr/bin/env python3
"""
Check if 0.0 sampling rate behavior is intended or a bug
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/aws-lambda-powertools_env/lib/python3.13/site-packages')

from aws_lambda_powertools.logging import Logger
from unittest.mock import patch
import logging

print("Testing 0.0 sampling rate behavior")
print("="*60)
print()

# According to documentation, sampling_rate of 0.0 should mean 0% sampling
# This means DEBUG level should NEVER be set

print("Expected: sampling_rate=0.0 means 0% sampling (never DEBUG)")
print("Testing with different random values...")
print()

test_randoms = [0.0, 0.001, 0.1, 0.5, 0.999, 1.0]

for rand_val in test_randoms:
    with patch('random.random', return_value=rand_val):
        logger = Logger(service="test", sampling_rate=0.0, level="INFO")
        
        print(f"random.random() = {rand_val:5.3f}")
        print(f"  Condition: {rand_val} <= 0.0 = {rand_val <= 0.0}")
        print(f"  Logger level: {logging.getLevelName(logger.log_level)}")
        
        if rand_val <= 0.0:
            print(f"  -> DEBUG set (sampling triggered)")
        else:
            print(f"  -> INFO kept (no sampling)")
        
        # Check for bug
        if rand_val == 0.0 and logger.log_level == logging.DEBUG:
            print("  ⚠️  EDGE CASE BUG: 0.0 sampling should mean NO sampling!")
        print()

print("\nBug Analysis:")
print("-" * 40)
print("The condition `random.random() <= sampling_rate` has an edge case:")
print("When sampling_rate=0.0 and random.random()=0.0, the condition is True")
print("This means DEBUG level is set, even though 0% sampling should mean NEVER DEBUG")
print()
print("This is likely a bug because:")
print("1. 0% sampling should mean no debug logging ever")
print("2. The probability of random.random() == 0.0 is extremely low but possible")
print("3. The documentation says 'ranging from 0 to 1' suggesting 0% to 100%")