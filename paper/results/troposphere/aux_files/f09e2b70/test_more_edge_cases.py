"""Test more edge cases for the boolean validator bug"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.validators import boolean
from decimal import Decimal

# Test various numeric types that might pass incorrectly
test_values = [
    0.0,           # float zero
    1.0,           # float one
    False,         # bool (which is valid)
    True,          # bool (which is valid)
    Decimal('0'),  # Decimal zero
    Decimal('1'),  # Decimal one
    0j,            # complex zero
    1+0j,          # complex one
]

for value in test_values:
    try:
        result = boolean(value)
        print(f"boolean({value!r}) = {result} (type: {type(value).__name__})")
    except ValueError as e:
        print(f"boolean({value!r}) raised ValueError")