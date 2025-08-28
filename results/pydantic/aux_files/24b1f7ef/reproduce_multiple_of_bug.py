"""Investigation of the multiple_of issue with very small floats."""

from typing import Annotated
from pydantic import BaseModel, ValidationError
from pydantic.experimental.pipeline import validate_as

# The failing value from the test
value = 4.132688558791042e-184
divisor = 0.5

print(f"Testing value: {value}")
print(f"Divisor: {divisor}")
print(f"Python's modulo result: {value % divisor}")
print(f"Is it effectively zero? {value % divisor == 0}")
print(f"Is value < divisor? {value < divisor}")

# The issue is likely that very small values (< divisor) are being incorrectly validated
# Let's test this hypothesis

class MultipleOfModel(BaseModel):
    field: Annotated[float, validate_as(float).multiple_of(divisor)]

try:
    result = MultipleOfModel(field=value)
    print(f"Validation passed! Result: {result.field}")
except ValidationError as e:
    print(f"Validation failed: {e}")
    
print("\n--- Testing the pattern ---")
print("Testing values smaller than the divisor:")

test_values = [
    0.0,  # Should pass (0 is multiple of everything)
    0.1,  # < 0.5, not a multiple
    0.25, # < 0.5, not a multiple  
    1e-10,  # Very small, < 0.5
    1e-100,  # Even smaller
    1e-200,  # Extremely small
]

for val in test_values:
    try:
        result = MultipleOfModel(field=val)
        remainder = val % divisor
        print(f"  {val:g}: PASSED (remainder={remainder:g})")
    except ValidationError:
        remainder = val % divisor
        print(f"  {val:g}: FAILED (remainder={remainder:g})")

print("\n--- Analysis ---")
print("For very small positive numbers x where 0 < x < divisor:")
print(f"  x % divisor = x (the number itself)")
print(f"  This is NOT zero, so they are NOT multiples of divisor")
print(f"  Example: {1e-100} % {divisor} = {1e-100 % divisor}")
print("\nConclusion: This appears to be correct behavior, not a bug.")
print("Very small numbers are only multiples of the divisor if they are exactly 0.")