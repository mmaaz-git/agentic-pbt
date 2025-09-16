"""
Focused test demonstrating the numeric type coercion bug in troposphere.supportapp.boolean
"""
import troposphere.supportapp as mod
from decimal import Decimal
import numpy as np


def test_undocumented_float_acceptance():
    """The boolean function accepts float types even though only int is listed."""
    # According to the source code, only these values should be accepted:
    # True values: [True, 1, "1", "true", "True"]
    # False values: [False, 0, "0", "false", "False"]
    
    # But float 1.0 and 0.0 are accepted due to == comparison in 'in' operator
    assert mod.boolean(1.0) is True  # Not in list but accepted!
    assert mod.boolean(0.0) is False  # Not in list but accepted!
    
    # String representations are correctly rejected
    try:
        mod.boolean("1.0")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass  # Expected
        
    try:
        mod.boolean("0.0")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass  # Expected


def test_complex_number_acceptance():
    """Complex numbers equal to 1 or 0 are incorrectly accepted."""
    # Complex numbers are definitely not intended to be valid boolean inputs
    assert mod.boolean(complex(1, 0)) is True  # Bug: accepts complex(1, 0)
    assert mod.boolean(complex(0, 0)) is False  # Bug: accepts complex(0, 0)
    
    # But complex(1, 1) is correctly rejected
    try:
        mod.boolean(complex(1, 1))
        assert False, "Should have raised ValueError"
    except ValueError:
        pass  # Expected


def test_decimal_acceptance():
    """Decimal types equal to 1 or 0 are incorrectly accepted."""
    # Decimal is not in the explicit list but is accepted
    assert mod.boolean(Decimal('1')) is True  # Bug: accepts Decimal('1')
    assert mod.boolean(Decimal('0')) is False  # Bug: accepts Decimal('0')
    
    # But Decimal('2') is correctly rejected
    try:
        mod.boolean(Decimal('2'))
        assert False, "Should have raised ValueError"
    except ValueError:
        pass  # Expected


def test_numpy_type_acceptance():
    """NumPy numeric types are incorrectly accepted."""
    # NumPy types are definitely not intended inputs
    assert mod.boolean(np.int64(1)) is True  # Bug: accepts np.int64(1)
    assert mod.boolean(np.int64(0)) is False  # Bug: accepts np.int64(0)
    assert mod.boolean(np.float64(1.0)) is True  # Bug: accepts np.float64(1.0)
    assert mod.boolean(np.float64(0.0)) is False  # Bug: accepts np.float64(0.0)


if __name__ == "__main__":
    test_undocumented_float_acceptance()
    print("✓ Float acceptance test passed (bug demonstrated)")
    
    test_complex_number_acceptance()
    print("✓ Complex number acceptance test passed (bug demonstrated)")
    
    test_decimal_acceptance()
    print("✓ Decimal acceptance test passed (bug demonstrated)")
    
    test_numpy_type_acceptance()
    print("✓ NumPy type acceptance test passed (bug demonstrated)")
    
    print("\nAll tests passed, demonstrating the numeric type coercion bug.")