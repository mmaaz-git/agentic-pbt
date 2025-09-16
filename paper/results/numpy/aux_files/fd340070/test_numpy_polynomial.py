import numpy as np
import numpy.polynomial.polynomial as poly
from hypothesis import given, strategies as st, assume, settings
import pytest
import math


safe_floats = st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6)
polynomial_coeffs = st.lists(safe_floats, min_size=1, max_size=10)
nonzero_polynomial_coeffs = st.lists(safe_floats, min_size=1, max_size=10).filter(
    lambda c: not all(abs(x) < 1e-10 for x in c)
)


@given(polynomial_coeffs, polynomial_coeffs)
def test_polyadd_commutative(c1, c2):
    """Addition should be commutative: c1 + c2 = c2 + c1"""
    result1 = poly.polyadd(c1, c2)
    result2 = poly.polyadd(c2, c1)
    assert np.allclose(result1, result2, rtol=1e-10, atol=1e-10)


@given(polynomial_coeffs, polynomial_coeffs)
def test_polysub_inverse_of_add(c1, c2):
    """Subtraction should be inverse of addition: (c1 + c2) - c2 = c1"""
    sum_poly = poly.polyadd(c1, c2)
    result = poly.polysub(sum_poly, c2)
    c1_trimmed = poly.polytrim(c1, tol=1e-10)
    result_trimmed = poly.polytrim(result, tol=1e-10)
    
    if len(c1_trimmed) == 0:
        c1_trimmed = [0]
    if len(result_trimmed) == 0:
        result_trimmed = [0]
    
    assert np.allclose(c1_trimmed, result_trimmed, rtol=1e-10, atol=1e-10)


@given(polynomial_coeffs)
def test_polymul_identity(c):
    """Multiplying by [1] should give the same polynomial"""
    result = poly.polymul(c, [1])
    c_trimmed = poly.polytrim(c, tol=1e-10)
    result_trimmed = poly.polytrim(result, tol=1e-10)
    
    if len(c_trimmed) == 0:
        c_trimmed = [0]
    if len(result_trimmed) == 0:
        result_trimmed = [0]
    
    assert np.allclose(c_trimmed, result_trimmed, rtol=1e-10, atol=1e-10)


@given(polynomial_coeffs)
def test_polymul_zero(c):
    """Multiplying by [0] should give zero polynomial"""
    result = poly.polymul(c, [0])
    assert np.allclose(result, [0], rtol=1e-10, atol=1e-10)


@given(polynomial_coeffs, polynomial_coeffs)
def test_polymul_commutative(c1, c2):
    """Multiplication should be commutative: c1 * c2 = c2 * c1"""
    result1 = poly.polymul(c1, c2)
    result2 = poly.polymul(c2, c1)
    assert np.allclose(result1, result2, rtol=1e-10, atol=1e-10)


@given(polynomial_coeffs, nonzero_polynomial_coeffs)
def test_polydiv_property(c1, c2):
    """Division property: c1 = q * c2 + r where deg(r) < deg(c2)"""
    q, r = poly.polydiv(c1, c2)
    
    # Reconstruct c1 from quotient and remainder
    reconstructed = poly.polyadd(poly.polymul(q, c2), r)
    
    c1_trimmed = poly.polytrim(c1, tol=1e-10)
    reconstructed_trimmed = poly.polytrim(reconstructed, tol=1e-10)
    
    if len(c1_trimmed) == 0:
        c1_trimmed = [0]
    if len(reconstructed_trimmed) == 0:
        reconstructed_trimmed = [0]
    
    assert np.allclose(c1_trimmed, reconstructed_trimmed, rtol=1e-8, atol=1e-8)
    
    # Check degree constraint
    r_trimmed = poly.polytrim(r, tol=1e-10)
    c2_trimmed = poly.polytrim(c2, tol=1e-10)
    assert len(r_trimmed) < len(c2_trimmed) or len(r_trimmed) <= 1


@given(polynomial_coeffs)
def test_polyder_polyint_inverse(c):
    """Derivative and integration should be approximate inverses"""
    if len(c) == 1:
        return  # Skip constant polynomials
    
    # Differentiate then integrate
    deriv = poly.polyder(c)
    integ = poly.polyint(deriv)
    
    # The result should be c minus its constant term
    expected = c.copy()
    expected[0] = 0  # Integration constant is 0
    
    # Only check non-constant terms
    if len(c) > 1:
        assert np.allclose(integ[1:], expected[1:], rtol=1e-10, atol=1e-10)


@given(st.lists(safe_floats, min_size=2, max_size=8))
def test_roots_fromroots_roundtrip(roots):
    """polyfromroots(roots) should give a polynomial with those roots"""
    assume(len(roots) == len(set(roots)))  # Avoid duplicate roots for simplicity
    assume(all(abs(r) < 100 for r in roots))  # Keep roots reasonable
    
    # Generate polynomial from roots
    coeffs = poly.polyfromroots(roots)
    
    # Find roots of the generated polynomial
    computed_roots = poly.polyroots(coeffs)
    
    # Sort both sets of roots for comparison
    roots_sorted = np.sort(np.array(roots))
    computed_sorted = np.sort(computed_roots)
    
    # Check if roots match (with some tolerance for numerical errors)
    if len(roots) == len(computed_roots):
        assert np.allclose(roots_sorted, computed_sorted, rtol=1e-6, atol=1e-6)


@given(polynomial_coeffs)
def test_polyval_at_zero(c):
    """Evaluating polynomial at 0 should give the constant term"""
    result = poly.polyval(0, c)
    expected = c[0] if c else 0
    assert np.isclose(result, expected, rtol=1e-10, atol=1e-10)


@given(polynomial_coeffs, safe_floats)
def test_polyval_linear(c, x):
    """For linear polynomial [a, b], polyval should give a + b*x"""
    if len(c) > 2:
        c = c[:2]  # Take only first two coefficients
    
    result = poly.polyval(x, c)
    
    if len(c) == 0:
        expected = 0
    elif len(c) == 1:
        expected = c[0]
    else:
        expected = c[0] + c[1] * x
    
    assert np.isclose(result, expected, rtol=1e-10, atol=1e-10)


@given(polynomial_coeffs, polynomial_coeffs, polynomial_coeffs)
def test_polyadd_associative(c1, c2, c3):
    """Addition should be associative: (c1 + c2) + c3 = c1 + (c2 + c3)"""
    result1 = poly.polyadd(poly.polyadd(c1, c2), c3)
    result2 = poly.polyadd(c1, poly.polyadd(c2, c3))
    assert np.allclose(result1, result2, rtol=1e-10, atol=1e-10)


@given(polynomial_coeffs, polynomial_coeffs, polynomial_coeffs)
def test_polymul_associative(c1, c2, c3):
    """Multiplication should be associative: (c1 * c2) * c3 = c1 * (c2 * c3)"""
    # Limit size to prevent numerical issues
    c1 = c1[:4]
    c2 = c2[:4]
    c3 = c3[:4]
    
    result1 = poly.polymul(poly.polymul(c1, c2), c3)
    result2 = poly.polymul(c1, poly.polymul(c2, c3))
    assert np.allclose(result1, result2, rtol=1e-8, atol=1e-8)


@given(polynomial_coeffs, polynomial_coeffs, polynomial_coeffs)
def test_polymul_distributive(c1, c2, c3):
    """Multiplication should be distributive: c1 * (c2 + c3) = c1*c2 + c1*c3"""
    # Limit size to prevent numerical issues
    c1 = c1[:4]
    c2 = c2[:4]
    c3 = c3[:4]
    
    # Left side: c1 * (c2 + c3)
    sum_23 = poly.polyadd(c2, c3)
    left = poly.polymul(c1, sum_23)
    
    # Right side: c1*c2 + c1*c3
    prod1 = poly.polymul(c1, c2)
    prod2 = poly.polymul(c1, c3)
    right = poly.polyadd(prod1, prod2)
    
    assert np.allclose(left, right, rtol=1e-8, atol=1e-8)


@given(nonzero_polynomial_coeffs)
def test_polydiv_by_self(c):
    """Dividing polynomial by itself should give quotient [1] and remainder [0]"""
    q, r = poly.polydiv(c, c)
    
    q_trimmed = poly.polytrim(q, tol=1e-10)
    r_trimmed = poly.polytrim(r, tol=1e-10)
    
    assert np.allclose(q_trimmed, [1], rtol=1e-8, atol=1e-8)
    assert len(r_trimmed) == 0 or np.allclose(r_trimmed, [0], rtol=1e-8, atol=1e-8)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])