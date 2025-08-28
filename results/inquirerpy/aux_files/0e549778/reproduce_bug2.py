"""Minimal reproduction of NumberPrompt negative toggle bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/inquirerpy_env/lib/python3.13/site-packages')

from InquirerPy.prompts.number import NumberPrompt

# Bug 2: Negative toggle doesn't work for value 0
print("Bug 2: Negative toggle fails for zero")
print("-" * 40)

prompt = NumberPrompt(
    message="Test",
    default=0
)

# Set buffer to "0"
prompt._whole_buffer.text = "0"
print(f"Initial buffer text: '{prompt._whole_buffer.text}'")

# Toggle negative (should become "-0")
prompt._handle_negative_toggle(None)
print(f"After first toggle: '{prompt._whole_buffer.text}'")
print(f"Expected: '-0', Got: '{prompt._whole_buffer.text}'")

if prompt._whole_buffer.text != "-0":
    print("BUG: Negative toggle doesn't work for '0'")
    
# Let's check the code to understand why
print("\nLooking at the code (lines 509-511):")
print("if self._whole_buffer.text == '-':")
print("    self._whole_buffer.text = '0'")
print("    return")
print("\nThis special case causes '0' to not get negated!")