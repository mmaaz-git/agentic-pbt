"""Bug demonstration: integer validator accepts non-integer values"""

from decimal import Decimal
from fractions import Fraction
import troposphere.validators as validators


def test_integer_validator_accepts_non_integers():
    """Demonstrate that integer validator incorrectly accepts non-integer values"""
    
    # These non-integer values are incorrectly accepted
    problematic_values = [
        Decimal('0.5'),
        Decimal('1.7'),
        Decimal('-2.3'),
        3.14,  # Regular float
        2.5,
        -7.89,
        float('1.1'),
    ]
    
    print("Testing non-integer values that should be rejected:")
    for value in problematic_values:
        try:
            result = validators.integer(value)
            print(f"  {value} ({type(value).__name__}) -> ACCEPTED (returns {result})")
            print(f"    This is WRONG: {value} is not an integer!")
            print(f"    int({value}) = {int(value)} (truncates)")
        except ValueError:
            print(f"  {value} ({type(value).__name__}) -> correctly rejected")
    
    print("\n\nComparing with integer-valued decimals (which should be accepted):")
    integer_decimals = [
        Decimal('1.0'),
        Decimal('0'),
        Decimal('-5.0'),
    ]
    
    for value in integer_decimals:
        try:
            result = validators.integer(value)
            is_integer = (value == int(value))
            print(f"  {value} -> accepted (is_integer: {is_integer})")
        except ValueError:
            print(f"  {value} -> rejected")


if __name__ == "__main__":
    test_integer_validator_accepts_non_integers()