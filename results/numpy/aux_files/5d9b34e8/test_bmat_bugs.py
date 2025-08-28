import numpy as np
from hypothesis import given, strategies as st, assume
import warnings
import sys

warnings.filterwarnings("ignore", category=PendingDeprecationWarning)

# Test bmat with string mode for potential variable injection
def test_bmat_string_evaluation():
    """Test bmat string mode for potential security/logic issues"""
    
    print("Testing bmat string evaluation mode:")
    print("=" * 60)
    
    # Normal usage
    A = np.matrix('1 2; 3 4')
    B = np.matrix('5 6; 7 8')
    
    result = np.bmat('A B; B A')
    print("Normal usage works fine:")
    print(f"bmat('A B; B A') with A={A.tolist()}, B={B.tolist()}")
    print(f"Result shape: {result.shape}")
    
    # Test with missing variable
    print("\nTest 1: Missing variable")
    try:
        result = np.bmat('A C; B A')  # C is not defined
        print(f"  Unexpected success: {result}")
    except NameError as e:
        print(f"  Expected NameError: {e}")
    
    # Test with Python keywords
    print("\nTest 2: Python keywords as variable names")
    try:
        result = np.bmat('if else; for while')
        print(f"  Unexpected success: {result}")
    except (NameError, SyntaxError) as e:
        print(f"  Expected error: {type(e).__name__}: {e}")
    
    # Test with special names
    print("\nTest 3: Special Python names")
    special_names = ['__name__', '__file__', '__doc__', 'None', 'True', 'False']
    for name in special_names:
        try:
            result = np.bmat(f'{name}')
            print(f"  '{name}' -> {type(result)}, shape: {result.shape if hasattr(result, 'shape') else 'N/A'}")
        except Exception as e:
            print(f"  '{name}' -> {type(e).__name__}: {e}")
    
    # Test variable shadowing
    print("\nTest 4: Variable shadowing")
    matrix = np.matrix('99 99; 99 99')  # Shadow the matrix class name
    try:
        result = np.bmat('matrix')
        print(f"  'matrix' variable (shadowing class) -> {result.tolist()}")
    except Exception as e:
        print(f"  Error: {type(e).__name__}: {e}")
    
    # Test with expressions (should fail)
    print("\nTest 5: Expressions in string")
    expressions = ['A+B', 'A*2', 'A.T', 'A[0]', 'A**2']
    for expr in expressions:
        try:
            result = np.bmat(expr)
            print(f"  '{expr}' -> Unexpected success!")
        except (NameError, SyntaxError) as e:
            print(f"  '{expr}' -> {type(e).__name__}: {e}")


def test_bmat_with_generator():
    """Test bmat with generator expressions"""
    print("\n" + "=" * 60)
    print("Testing bmat with generators and iterables:")
    
    # Create some matrices
    matrices = [np.matrix(f'{i} {i+1}; {i+2} {i+3}') for i in range(0, 8, 4)]
    
    # Test with generator
    gen = (m for m in matrices)
    try:
        result = np.bmat([list(gen)])
        print(f"Generator worked: shape {result.shape}")
    except Exception as e:
        print(f"Generator failed: {type(e).__name__}: {e}")
    
    # Test with iterator
    iter_matrices = iter(matrices)
    try:
        result = np.bmat([[next(iter_matrices), next(iter_matrices)]])
        print(f"Iterator worked: shape {result.shape}")
    except Exception as e:
        print(f"Iterator failed: {type(e).__name__}: {e}")


def test_bmat_dimension_mismatch():
    """Test bmat with mismatched dimensions"""
    print("\n" + "=" * 60)
    print("Testing bmat dimension mismatches:")
    
    # Different row heights
    m1 = np.matrix('1 2')  # 1x2
    m2 = np.matrix('3 4; 5 6')  # 2x2
    
    print("\nHorizontal concatenation with different heights:")
    try:
        result = np.bmat([[m1, m2]])
        print(f"  Unexpected success: {result.shape}")
    except ValueError as e:
        print(f"  Expected ValueError: {e}")
    
    # Different column widths
    m3 = np.matrix('1; 2')  # 2x1
    m4 = np.matrix('3 4; 5 6')  # 2x2
    
    print("\nVertical concatenation with different widths:")
    try:
        result = np.bmat([[m3], [m4]])
        print(f"  Unexpected success: {result.shape}")
    except ValueError as e:
        print(f"  Expected ValueError: {e}")
    
    # Empty matrices
    print("\nWith empty matrices:")
    empty = np.matrix(np.empty((0, 0)))
    m5 = np.matrix('1 2; 3 4')
    
    try:
        result = np.bmat([[empty, m5]])
        print(f"  Empty + matrix horizontal: {result.shape}")
        print(f"  Result: {result}")
    except Exception as e:
        print(f"  Error: {type(e).__name__}: {e}")
    
    try:
        result = np.bmat([[empty], [m5]])
        print(f"  Empty + matrix vertical: {result.shape}")
        print(f"  Result: {result}")
    except Exception as e:
        print(f"  Error: {type(e).__name__}: {e}")


def test_bmat_with_none():
    """Test bmat with None values"""
    print("\n" + "=" * 60)
    print("Testing bmat with None:")
    
    m = np.matrix('1 2; 3 4')
    
    test_cases = [
        [[None, m]],
        [[m, None]],
        [[None], [m]],
        [[m], [None]],
        [[None, None], [m, m]],
    ]
    
    for i, case in enumerate(test_cases):
        try:
            result = np.bmat(case)
            print(f"  Case {i}: {case} -> shape {result.shape}")
            print(f"    Result: {result}")
        except Exception as e:
            print(f"  Case {i}: {case} -> {type(e).__name__}: {e}")


@given(st.lists(st.lists(st.floats(min_value=-10, max_value=10), min_size=1, max_size=3), min_size=1, max_size=3))
def test_bmat_property(data):
    """Property test for bmat"""
    # Make all rows same length
    if len(set(len(row) for row in data)) != 1:
        return
    
    m = np.matrix(data)
    
    # Test that [[m]] returns m
    result = np.bmat([[m]])
    assert np.allclose(result, m)
    
    # Test block diagonal
    result = np.bmat([[m, None], [None, m]])
    assert result.shape == (m.shape[0] * 2, m.shape[1] * 2)


if __name__ == "__main__":
    test_bmat_string_evaluation()
    test_bmat_with_generator()
    test_bmat_dimension_mismatch()
    test_bmat_with_none()
    
    print("\n" + "=" * 60)
    print("Running property tests...")
    test_bmat_property()
    print("Property tests passed")