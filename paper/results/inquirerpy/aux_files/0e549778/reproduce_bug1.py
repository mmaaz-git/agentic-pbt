"""Minimal reproduction of NumberPrompt float min/max constraint bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/inquirerpy_env/lib/python3.13/site-packages')

from decimal import Decimal
from InquirerPy.prompts.number import NumberPrompt

# Bug 1: Float values don't respect min/max constraints
print("Bug 1: Float min/max constraint violation")
print("-" * 40)

# Case 1: min_val > 0, but value stays at 0
prompt1 = NumberPrompt(
    message="Test",
    float_allowed=True,
    min_allowed=1.0,
    max_allowed=10.0,
    default=1.0
)

print(f"Created prompt with min=1.0, max=10.0")
print(f"Initial value: {prompt1.value}")

# Try to set value to 0 (below min)
prompt1.value = Decimal("0.0")
print(f"After setting value to 0.0: {prompt1.value}")
print(f"Expected: >= 1.0, Got: {prompt1.value}")
print(f"BUG: Value is {prompt1.value} but should be clamped to min_allowed=1.0")

print()

# Case 2: max_val < 0, but value stays at 0  
prompt2 = NumberPrompt(
    message="Test",
    float_allowed=True,
    min_allowed=-10.0,
    max_allowed=-1.0,
    default=-5.0
)

print(f"Created prompt with min=-10.0, max=-1.0")
print(f"Initial value: {prompt2.value}")

# Try to set value to 0 (above max)
prompt2.value = Decimal("0.0")
print(f"After setting value to 0.0: {prompt2.value}")
print(f"Expected: <= -1.0, Got: {prompt2.value}")
print(f"BUG: Value is {prompt2.value} but should be clamped to max_allowed=-1.0")