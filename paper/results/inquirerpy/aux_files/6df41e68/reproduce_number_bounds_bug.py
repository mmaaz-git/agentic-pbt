#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/inquirerpy_env/lib/python3.13/site-packages')

from InquirerPy.prompts import NumberPrompt
from decimal import Decimal

# Bug 1: Min/max bounds not enforced on initialization
print("Testing NumberPrompt min/max bounds enforcement...")
print()

# Test case 1: Default value below minimum
print("Test 1: Default value (0) below minimum (1)")
prompt1 = NumberPrompt(
    message="Test",
    min_allowed=1.0,
    max_allowed=10.0,
    default=0.0,
    float_allowed=True
)
print(f"  min_allowed: 1.0")
print(f"  max_allowed: 10.0")
print(f"  default: 0.0")
print(f"  Expected value: >= 1.0")
print(f"  Actual value: {prompt1.value}")
print(f"  BUG: Value is {prompt1.value}, should be clamped to min (1.0)")
print()

# Test case 2: Default value above maximum
print("Test 2: Default value (100) above maximum (10)")
prompt2 = NumberPrompt(
    message="Test",
    min_allowed=1.0,
    max_allowed=10.0,
    default=100.0,
    float_allowed=True
)
print(f"  min_allowed: 1.0")
print(f"  max_allowed: 10.0")
print(f"  default: 100.0")
print(f"  Expected value: <= 10.0")
print(f"  Actual value: {prompt2.value}")
print(f"  BUG: Value is {prompt2.value}, should be clamped to max (10.0)")
print()

# Test case 3: With negative bounds
print("Test 3: Default value (0) above maximum (-1)")
prompt3 = NumberPrompt(
    message="Test",
    min_allowed=-10.0,
    max_allowed=-1.0,
    default=0.0,
    float_allowed=True
)
print(f"  min_allowed: -10.0")
print(f"  max_allowed: -1.0")
print(f"  default: 0.0")
print(f"  Expected value: <= -1.0")
print(f"  Actual value: {prompt3.value}")
print(f"  BUG: Value is {prompt3.value}, should be clamped to max (-1.0)")
print()

print("="*60)
print("Root cause: The NumberPrompt doesn't enforce min/max bounds")
print("on the default value during initialization.")
print("The bounds are only enforced when the value is set via")
print("the value.setter, but not when accessed initially.")