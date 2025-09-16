"""Property-based tests for packaging.licenses.canonicalize_license_expression"""

import re
from hypothesis import given, strategies as st, assume, settings
from packaging.licenses import (
    canonicalize_license_expression,
    InvalidLicenseExpression,
    LICENSES,
    EXCEPTIONS,
)


# Strategies for generating license expressions
known_licenses = st.sampled_from(list(LICENSES.keys()))
known_exceptions = st.sampled_from(list(EXCEPTIONS.keys()))

# LicenseRef pattern
license_ref = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters=".-"),
    min_size=1,
    max_size=50
).map(lambda s: f"LicenseRef-{s}")

# Single license (either known or LicenseRef)
single_license = st.one_of(known_licenses, license_ref)

# License with optional plus
license_with_plus = st.builds(
    lambda lic, plus: f"{lic}+" if plus else lic,
    single_license,
    st.booleans()
)

# License with optional exception
license_with_exception = st.builds(
    lambda lic, exc: f"{lic} WITH {exc}" if exc else lic,
    license_with_plus,
    st.one_of(st.none(), known_exceptions)
)

# Build complex expressions recursively (limited depth to avoid too complex)
def license_expression(max_depth=3):
    if max_depth <= 0:
        return license_with_exception
    
    return st.one_of(
        license_with_exception,
        st.builds(
            lambda left, op, right: f"{left} {op} {right}",
            license_expression(max_depth - 1),
            st.sampled_from(["AND", "OR"]),
            license_expression(max_depth - 1)
        ),
        st.builds(
            lambda expr: f"({expr})",
            license_expression(max_depth - 1)
        )
    )

valid_expression = license_expression()


@given(valid_expression)
@settings(max_examples=500)
def test_idempotence(expr):
    """Test that canonicalizing a canonicalized expression returns the same result."""
    try:
        canonicalized_once = canonicalize_license_expression(expr)
        canonicalized_twice = canonicalize_license_expression(canonicalized_once)
        assert canonicalized_once == canonicalized_twice, \
            f"Not idempotent: {expr} -> {canonicalized_once} -> {canonicalized_twice}"
    except InvalidLicenseExpression:
        # If the expression is invalid, that's fine for this test
        pass


@given(known_licenses)
def test_case_normalization(license_id):
    """Test that license IDs are case-normalized to their canonical form."""
    # Test various case variations
    variations = [
        license_id.lower(),
        license_id.upper(),
        license_id.capitalize(),
    ]
    
    canonical = canonicalize_license_expression(license_id)
    
    for variant in variations:
        result = canonicalize_license_expression(variant)
        assert result == canonical, \
            f"Case normalization failed: {variant} -> {result}, expected {canonical}"


@given(st.text(alphabet=st.characters(whitelist_categories=("Zs",)), min_size=1, max_size=10))
def test_whitespace_normalization(spaces):
    """Test that extra whitespace is normalized in expressions."""
    # Create expressions with varying whitespace
    expr_with_spaces = f"MIT{spaces}OR{spaces}Apache-2.0"
    expr_normal = "MIT OR Apache-2.0"
    
    result = canonicalize_license_expression(expr_with_spaces)
    expected = canonicalize_license_expression(expr_normal)
    
    assert result == expected, \
        f"Whitespace not normalized: {repr(expr_with_spaces)} -> {result}, expected {expected}"


@given(valid_expression)
def test_leading_trailing_whitespace(expr):
    """Test that leading and trailing whitespace is removed."""
    try:
        normal = canonicalize_license_expression(expr)
        with_spaces = canonicalize_license_expression(f"  {expr}  ")
        assert normal == with_spaces, \
            f"Leading/trailing whitespace not handled: '{expr}' vs '  {expr}  '"
    except InvalidLicenseExpression:
        pass


@given(st.lists(known_licenses, min_size=2, max_size=5))
def test_complex_expression_structure(licenses):
    """Test that complex nested expressions preserve logical structure."""
    # Build a complex expression
    expr = licenses[0]
    for i, lic in enumerate(licenses[1:], 1):
        if i % 2 == 0:
            expr = f"({expr}) AND {lic}"
        else:
            expr = f"{expr} OR {lic}"
    
    try:
        result = canonicalize_license_expression(expr)
        # The result should be a valid string
        assert isinstance(result, str)
        assert len(result) > 0
        
        # All original licenses should appear in the result
        for lic in licenses:
            assert lic in result or lic.upper() in result or lic.lower() in result, \
                f"License {lic} missing from result: {result}"
    except InvalidLicenseExpression:
        pass


@given(known_licenses, known_exceptions)
def test_with_clause_preservation(license_id, exception_id):
    """Test that WITH clauses are properly preserved."""
    expr = f"{license_id} WITH {exception_id}"
    result = canonicalize_license_expression(expr)
    
    # The WITH clause should be preserved
    assert "WITH" in result
    # Both parts should be in the result (possibly case-normalized)
    assert any(license_id.lower() in result.lower() or 
               license_id.upper() in result or 
               license_id in result for _ in [1])
    assert exception_id in result


@given(st.text(alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), 
                                      whitelist_characters=".-"), 
               min_size=0, max_size=50))
def test_license_ref_format(ref_suffix):
    """Test LicenseRef handling with various suffixes."""
    ref = f"LicenseRef-{ref_suffix}"
    
    try:
        result = canonicalize_license_expression(ref)
        # LicenseRef should be preserved as-is
        assert result == ref, f"LicenseRef modified: {ref} -> {result}"
    except InvalidLicenseExpression:
        # Check if it should have been valid according to the pattern
        pattern = re.compile(r"^[A-Za-z0-9.-]*$")
        if pattern.match(ref_suffix):
            # This should have been valid
            raise AssertionError(f"Valid LicenseRef rejected: {ref}")


@given(st.lists(st.sampled_from(["(", ")"]), min_size=1, max_size=10))
def test_unbalanced_parentheses(parens):
    """Test that unbalanced parentheses are rejected."""
    expr = "MIT " + "".join(parens) + " Apache-2.0"
    
    # Count parentheses
    open_count = expr.count("(")
    close_count = expr.count(")")
    
    if open_count != close_count:
        # Should raise InvalidLicenseExpression
        try:
            result = canonicalize_license_expression(expr)
            assert False, f"Unbalanced parentheses accepted: {expr} -> {result}"
        except InvalidLicenseExpression:
            pass  # Expected


@given(st.sampled_from(["AND", "OR", "WITH"]))
def test_operator_at_boundaries(operator):
    """Test that operators at expression boundaries are rejected."""
    # Operator at start
    expr_start = f"{operator} MIT"
    try:
        canonicalize_license_expression(expr_start)
        assert False, f"Operator at start accepted: {expr_start}"
    except InvalidLicenseExpression:
        pass  # Expected
    
    # Operator at end
    expr_end = f"MIT {operator}"
    try:
        canonicalize_license_expression(expr_end)
        assert False, f"Operator at end accepted: {expr_end}"
    except InvalidLicenseExpression:
        pass  # Expected