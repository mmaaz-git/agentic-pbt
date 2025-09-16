"""Minimal reproduction of the str_strip bug with control characters."""

from typing import Annotated
from pydantic import BaseModel
from pydantic.experimental.pipeline import validate_as

# Test with Unit Separator character
test_char = '\x1f'
print(f"Testing with character: {test_char!r}")
print(f"Python's str.strip() result: {test_char.strip()!r}")
print(f"Is it whitespace according to Python? {test_char.isspace()}")

class StripModel(BaseModel):
    value: Annotated[str, validate_as(str).str_strip()]

result = StripModel(value=test_char)
print(f"Pydantic pipeline str_strip() result: {result.value!r}")

# Check if they match
if result.value != test_char.strip():
    print("\nBUG CONFIRMED: str_strip() in pydantic.experimental.pipeline does not match Python's str.strip()")
    print(f"Expected (Python's strip): {test_char.strip()!r}")
    print(f"Got (Pydantic's strip): {result.value!r}")
    
    # Test with more control characters
    control_chars = ['\x00', '\x01', '\x1f', '\x7f', '\x0b', '\x0c']
    print("\nTesting more control characters:")
    for char in control_chars:
        result = StripModel(value=char)
        python_strip = char.strip()
        if result.value != python_strip:
            print(f"  {char!r}: Python strips to {python_strip!r}, Pydantic keeps {result.value!r}")
else:
    print("No bug found")