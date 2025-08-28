"""Test what happens when default is outside min/max bounds."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/inquirerpy_env/lib/python3.13/site-packages')

from InquirerPy.prompts.number import NumberPrompt

# Test: Default value outside bounds 
print("Testing default value outside bounds:")
print("-" * 40)

# Case 1: Default below min (float)
prompt1 = NumberPrompt(
    message="Test",
    float_allowed=True,
    min_allowed=5.0,
    max_allowed=10.0,
    default=1.0  # Below min
)
print(f"Float prompt with min=5.0, max=10.0, default=1.0")
print(f"Actual value: {prompt1.value}")
print(f"Expected: 5.0 (clamped to min)")
print()

# Case 2: Default above max (float)
prompt2 = NumberPrompt(
    message="Test",
    float_allowed=True,
    min_allowed=1.0,
    max_allowed=5.0,
    default=10.0  # Above max
)
print(f"Float prompt with min=1.0, max=5.0, default=10.0")
print(f"Actual value: {prompt2.value}")
print(f"Expected: 5.0 (clamped to max)")
print()

# Case 3: Default below min (int)
prompt3 = NumberPrompt(
    message="Test",
    float_allowed=False,
    min_allowed=5,
    max_allowed=10,
    default=1  # Below min
)
print(f"Int prompt with min=5, max=10, default=1")
print(f"Actual value: {prompt3.value}")
print(f"Expected: 5 (clamped to min)")