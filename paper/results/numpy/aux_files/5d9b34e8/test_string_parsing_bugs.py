import numpy as np
from hypothesis import given, strategies as st, assume, settings
import warnings
import ast

warnings.filterwarnings("ignore", category=PendingDeprecationWarning)

# Let's test the _convert_from_string function directly
from numpy.matrixlib.defmatrix import _convert_from_string

def test_convert_from_string_edge_cases():
    """Test _convert_from_string with problematic inputs"""
    
    # Test 1: Empty string after removing brackets
    print("Test 1: Empty string after bracket removal")
    try:
        result = _convert_from_string("[]")
        print(f"  Result: {result}")
    except Exception as e:
        print(f"  Exception: {type(e).__name__}: {e}")
    
    # Test 2: String with only brackets and semicolons
    print("\nTest 2: String with only structure, no data")
    test_cases = ["[];[]", "[;]", "[[]]", ";", ";;"]
    for s in test_cases:
        try:
            result = _convert_from_string(s)
            print(f"  '{s}' -> {result}")
        except Exception as e:
            print(f"  '{s}' -> {type(e).__name__}: {e}")
    
    # Test 3: Malformed numeric strings
    print("\nTest 3: Invalid numeric literals")
    test_cases = ["1.2.3", "1e", "1e+", "--1", "++1", "nan", "inf", "infinity"]
    for s in test_cases:
        try:
            result = _convert_from_string(s)
            print(f"  '{s}' -> {result}")
        except Exception as e:
            print(f"  '{s}' -> {type(e).__name__}: {e}")
    
    # Test 4: Mixed valid and invalid
    print("\nTest 4: Mixed valid/invalid in rows")
    try:
        result = _convert_from_string("1 2; 3")
        print(f"  '1 2; 3' -> {result}")
    except Exception as e:
        print(f"  '1 2; 3' -> {type(e).__name__}: {e}")
    
    # Test 5: Unicode and special characters
    print("\nTest 5: Unicode and special chars")
    test_cases = ["1\u00A02", "1\t2", "1\n2", "1\r\n2"]
    for s in test_cases:
        try:
            result = _convert_from_string(s)
            print(f"  '{repr(s)}' -> {result}")
        except Exception as e:
            print(f"  '{repr(s)}' -> {type(e).__name__}: {e}")


def test_matrix_string_construction_bugs():
    """Test np.matrix string constructor for bugs"""
    
    print("\n=== Testing np.matrix string constructor ===")
    
    # Test with expressions that ast.literal_eval can't handle
    print("\nTest: Expressions in string")
    test_cases = [
        "1+1 2; 3 4",
        "2**3 1; 2 3",
        "1/0 2; 3 4",
        "[1 2; 3 4]",  # Nested brackets
    ]
    
    for s in test_cases:
        try:
            m = np.matrix(s)
            print(f"  '{s}' -> matrix with shape {m.shape}")
            print(f"    Values: {m}")
        except Exception as e:
            print(f"  '{s}' -> {type(e).__name__}: {e}")
    
    # Test whitespace handling
    print("\nTest: Various whitespace patterns")
    test_cases = [
        "  1  2  ;  3  4  ",  # Extra spaces
        "1,2;3,4",  # Commas
        "1, 2; 3, 4",  # Mixed
        "1  ,  2  ;  3  ,  4",  # Spaces around commas
    ]
    
    for s in test_cases:
        try:
            m = np.matrix(s)
            print(f"  '{s}' -> shape {m.shape}, values: {m.tolist()}")
        except Exception as e:
            print(f"  '{s}' -> {type(e).__name__}: {e}")


@given(st.text(alphabet="0123456789.e+-; ,\t\n", min_size=1, max_size=50))
def test_matrix_string_fuzzing(s):
    """Fuzz test matrix string parsing"""
    try:
        m = np.matrix(s)
        # If it succeeds, verify it's a valid matrix
        assert isinstance(m, np.matrix)
        assert m.ndim == 2
        # Values should be finite
        if m.size > 0:
            assert np.all(np.isfinite(m))
    except (ValueError, SyntaxError, IndexError, TypeError) as e:
        # Expected exceptions for invalid input
        pass
    except Exception as e:
        # Unexpected exception - could be a bug
        print(f"\nUnexpected exception for input '{s}': {type(e).__name__}: {e}")
        raise


def test_literal_eval_edge_cases():
    """Test edge cases with ast.literal_eval usage"""
    print("\n=== Testing ast.literal_eval edge cases ===")
    
    # These should work with literal_eval
    valid_literals = ["1", "1.0", "1e5", "-1", "True", "False", "None"]
    
    for lit in valid_literals:
        try:
            result = ast.literal_eval(lit)
            print(f"  literal_eval('{lit}') = {result} (type: {type(result).__name__})")
        except Exception as e:
            print(f"  literal_eval('{lit}') -> {type(e).__name__}: {e}")
    
    # These should fail
    invalid_literals = ["1+1", "2**3", "__import__('os')", "lambda x: x"]
    
    for lit in invalid_literals:
        try:
            result = ast.literal_eval(lit)
            print(f"  literal_eval('{lit}') = {result} (UNEXPECTED SUCCESS)")
        except Exception as e:
            print(f"  literal_eval('{lit}') -> {type(e).__name__}: {e}")
    
    # Test in matrix context
    print("\nIn matrix context:")
    for lit in ["True False; False True", "None 1; 2 3", "1 True; False 0"]:
        try:
            m = np.matrix(lit)
            print(f"  matrix('{lit}') -> {m.tolist()}")
        except Exception as e:
            print(f"  matrix('{lit}') -> {type(e).__name__}: {e}")


if __name__ == "__main__":
    test_convert_from_string_edge_cases()
    test_matrix_string_construction_bugs()
    test_literal_eval_edge_cases()
    
    # Run hypothesis test
    print("\n=== Running hypothesis fuzzing ===")
    try:
        test_matrix_string_fuzzing()
        print("Fuzzing completed without finding bugs")
    except Exception as e:
        print(f"Fuzzing found issue: {e}")