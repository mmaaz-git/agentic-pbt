from hypothesis import given, strategies as st
from bs4.formatter import Formatter

@given(st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False))
def test_indent_float_handling(float_value):
    """Test that float indent values are handled consistently with integers."""
    formatter = Formatter(indent=float_value)
    
    # Floats should behave like their integer equivalents
    int_equivalent = int(float_value)
    int_formatter = Formatter(indent=int_equivalent)
    
    # The bug: floats always become single space instead of being converted to int
    assert formatter.indent == int_formatter.indent, \
        f"Float {float_value} produces '{formatter.indent}' but int {int_equivalent} produces '{int_formatter.indent}'"