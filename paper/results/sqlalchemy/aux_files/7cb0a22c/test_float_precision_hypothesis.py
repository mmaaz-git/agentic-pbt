"""
Property-based test to find Float precision loss bugs in SQLAlchemy.
"""
from decimal import Decimal
from hypothesis import given, strategies as st, settings
import sqlalchemy.types as types


@given(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e20, max_value=1e20))
@settings(max_examples=1000)
def test_float_to_decimal_precision_property(value):
    """Test that Float type preserves precision when converting to Decimal."""
    
    # Create Float type with asdecimal=True 
    ft = types.Float(asdecimal=True, decimal_return_scale=10)
    
    class MockDialect:
        supports_native_decimal = False
    
    dialect = MockDialect()
    
    # Get the result processor
    result_proc = ft.result_processor(dialect, None)
    
    if result_proc and value is not None:
        # Process the value
        retrieved = result_proc(value)
        
        # Convert the original float to string then to Decimal (preserves precision)
        expected = Decimal(str(value))
        
        # The bug: SQLAlchemy's processor formats to fixed decimal places
        # This loses precision for floats with more significant digits
        
        # Check if precision was lost
        if float(expected) == value and float(retrieved) != value:
            # Found a case where precision was lost
            print(f"\nFound precision loss for value: {value}")
            print(f"  Original:  {value:.20f}")
            print(f"  Retrieved: {float(retrieved):.20f}")
            print(f"  Expected:  {float(expected):.20f}")
            print(f"  Lost:      {value - float(retrieved):.20e}")
            
            # This assertion will fail, demonstrating the bug
            assert float(retrieved) == value, f"Precision lost for {value}"


if __name__ == "__main__":
    # Run the test
    test_float_to_decimal_precision_property()