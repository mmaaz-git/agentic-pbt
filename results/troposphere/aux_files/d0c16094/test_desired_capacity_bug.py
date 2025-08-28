#!/usr/bin/env python3
"""Verify the DesiredCapacity validation bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.m2 as m2

# Test 1: Negative desired capacity (should be invalid)
config1 = m2.HighAvailabilityConfig(DesiredCapacity=-5)
print("HighAvailabilityConfig with negative DesiredCapacity:")
print(config1.to_dict())

# Test 2: Zero desired capacity (should be invalid, minimum is 1)
config2 = m2.HighAvailabilityConfig(DesiredCapacity=0)
print("\nHighAvailabilityConfig with zero DesiredCapacity:")
print(config2.to_dict())

# Test 3: Desired capacity over 100 (should be invalid, maximum is 100)
config3 = m2.HighAvailabilityConfig(DesiredCapacity=1000)
print("\nHighAvailabilityConfig with DesiredCapacity=1000:")
print(config3.to_dict())

# According to AWS docs:
# - Minimum: 1
# - Maximum: 100
# But troposphere accepts any integer value