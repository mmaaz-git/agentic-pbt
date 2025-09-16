#!/usr/bin/env python3

import sys
import types

# Mock cfn_flip
sys.modules['cfn_flip'] = types.ModuleType('cfn_flip')

# Add troposphere to path
sys.path.insert(0, '/root/hypothesis-llm/worker_/1/troposphere-4.9.3')

from troposphere.ivschat import Room

# Test if the bug affects Room creation
print("Testing if the bug affects Room creation with infinity values...")

try:
    room = Room('TestRoom', MaximumMessageLength=float('inf'))
    print("Room created with MaximumMessageLength=inf (unexpected!)")
except ValueError as e:
    print(f"ValueError (expected): {e}")
except OverflowError as e:
    print(f"OverflowError (bug propagated to Room): {e}")
    print("BUG CONFIRMED: Room crashes with OverflowError instead of ValueError")

print("\nTesting with -infinity...")
try:
    room = Room('TestRoom', MaximumMessageRatePerSecond=float('-inf'))
    print("Room created with MaximumMessageRatePerSecond=-inf (unexpected!)")
except ValueError as e:
    print(f"ValueError (expected): {e}")
except OverflowError as e:
    print(f"OverflowError (bug propagated to Room): {e}")
    print("BUG CONFIRMED: Room crashes with OverflowError instead of ValueError")

print("\nThis affects real usage:")
print("- Users might pass float values expecting validation")
print("- The validator should consistently raise ValueError for invalid inputs")
print("- Instead, it raises OverflowError for infinity values")
print("- This inconsistent error handling can break error handling code")