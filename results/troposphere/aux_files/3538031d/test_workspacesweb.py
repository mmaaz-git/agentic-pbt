import math
from hypothesis import given, assume, strategies as st
import pytest
import troposphere.workspacesweb as target_module


# Test 1: double() function identity property - it should return input unchanged for valid values
@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text().filter(lambda s: s.strip() and s.strip().replace('-', '').replace('+', '').replace('.', '').replace('e', '').replace('E', '').isdigit()),
    st.booleans()
))
def test_double_identity_property(x):
    """double() should return the input unchanged for valid float-convertible values"""
    # First check if float() would accept this
    try:
        float(x)
        can_convert = True
    except (ValueError, TypeError):
        can_convert = False
    
    if can_convert:
        result = target_module.double(x)
        assert result == x, f"double({x!r}) returned {result!r} instead of {x!r}"


# Test 2: double() should accept everything that float() accepts
@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=True, allow_infinity=True),
    st.decimals(allow_nan=True, allow_infinity=True),
    st.fractions(),
    st.complex_numbers().map(lambda c: c.real),  # Just the real part
    st.sampled_from([True, False]),
    st.sampled_from(["123", "12.34", "-45.67", "1e10", "1E10", "-1.23e-4", "inf", "-inf", "nan"])
))
def test_double_accepts_float_compatible(x):
    """double() should accept any value that float() accepts"""
    try:
        expected = float(x)
        is_valid = True
    except (ValueError, TypeError):
        is_valid = False
    
    if is_valid:
        try:
            result = target_module.double(x)
            # It should return the original value, not the converted float
            assert result == x
        except ValueError:
            pytest.fail(f"double() rejected {x!r} which float() accepts")


# Test 3: double() error message format
@given(st.one_of(
    st.none(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers()),
    st.text().filter(lambda s: not s.strip() or not any(c.isdigit() for c in s)),
    st.sampled_from([[], {}, set(), object(), lambda x: x])
))
def test_double_error_message(x):
    """double() should raise ValueError with specific message format for invalid inputs"""
    # First verify float() would reject this
    try:
        float(x)
        can_convert = True
    except (ValueError, TypeError):
        can_convert = False
    
    if not can_convert:
        with pytest.raises(ValueError) as exc_info:
            target_module.double(x)
        assert str(exc_info.value) == f"{x!r} is not a valid double"


# Test 4: InlineRedactionPattern with ConfidenceLevel
@given(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10))
def test_inline_redaction_pattern_confidence_level(confidence):
    """InlineRedactionPattern should accept and preserve numeric ConfidenceLevel values"""
    pattern = target_module.InlineRedactionPattern(
        ConfidenceLevel=confidence,
        RedactionPlaceHolder=target_module.RedactionPlaceHolder(
            RedactionPlaceHolderType='Text'
        )
    )
    
    result_dict = pattern.to_dict()
    assert 'ConfidenceLevel' in result_dict
    assert result_dict['ConfidenceLevel'] == confidence


# Test 5: Edge case - string numbers for double()
@given(st.text())
def test_double_string_numbers(s):
    """double() behavior with string inputs should match float() behavior"""
    try:
        float(s)
        float_accepts = True
    except (ValueError, TypeError):
        float_accepts = False
    
    if float_accepts:
        result = target_module.double(s)
        assert result == s  # Should return unchanged
    else:
        with pytest.raises(ValueError) as exc_info:
            target_module.double(s)
        assert str(exc_info.value) == f"{s!r} is not a valid double"


# Test 6: Special numeric strings
@given(st.sampled_from(["infinity", "INFINITY", "Infinity", "+Infinity", "-Infinity", 
                        "NaN", "nan", "NAN", "+nan", "-nan"]))
def test_double_special_strings(s):
    """double() should handle special float strings like 'inf' and 'nan'"""
    # Python's float() accepts these
    try:
        float_val = float(s)
        # double should accept and return unchanged
        result = target_module.double(s)
        assert result == s
    except ValueError:
        # If float() rejects it, double() should too
        with pytest.raises(ValueError):
            target_module.double(s)