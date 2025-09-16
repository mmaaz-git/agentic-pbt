"""
Demonstrates precision loss bug in SQLAlchemy Float type with decimal conversion.
"""
from decimal import Decimal
import sqlalchemy.types as types


def test_float_decimal_precision_loss():
    """Demonstrate that Float type loses precision when converting to Decimal."""
    
    # This float has more than 10 digits after the decimal point
    original_float = 6.103515625e-05  # 0.00006103515625
    
    # Create Float type with asdecimal=True and decimal_return_scale=10
    ft = types.Float(asdecimal=True, decimal_return_scale=10)
    
    # Mock dialect
    class MockDialect:
        supports_native_decimal = False
    
    dialect = MockDialect()
    
    # Get the result processor (simulates retrieving from DB)
    result_proc = ft.result_processor(dialect, None)
    
    # Process the float through the result processor
    retrieved_decimal = result_proc(original_float)
    
    print(f"Original float:     {original_float:.15f}")
    print(f"Original as string: {original_float}")
    print(f"Retrieved Decimal:  {retrieved_decimal}")
    print(f"Back to float:      {float(retrieved_decimal):.15f}")
    print(f"Precision lost:     {original_float - float(retrieved_decimal):.15e}")
    
    # The issue: the processor uses string formatting with fixed decimal places
    # This truncates the precision to 10 decimal places
    
    # What happens internally:
    scale = 10
    fstring = "%%.%df" % scale  # Creates "%.10f"
    formatted = fstring % original_float  # Formats to 10 decimal places
    print(f"\nInternal formatting: '{formatted}'")
    print(f"This loses precision after 10 decimal places")
    
    # The correct way would be to convert directly:
    correct_decimal = Decimal(str(original_float))
    print(f"\nCorrect conversion: {correct_decimal}")
    print(f"Correct to float:   {float(correct_decimal):.15f}")
    
    # Assert the bug exists
    assert float(retrieved_decimal) != original_float
    assert float(correct_decimal) == original_float
    
    print("\n✓ Bug confirmed: Float type loses precision with decimal conversion")


if __name__ == "__main__":
    test_float_decimal_precision_loss()