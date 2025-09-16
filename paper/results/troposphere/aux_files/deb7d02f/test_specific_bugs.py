import pytest
from hypothesis import given, settings, strategies as st, assume

import troposphere.quicksight as qs


# Test for inconsistency in boolean handling 
def test_boolean_numeric_edge_cases():
    """Test specific numeric edge cases for boolean validator."""
    # Test that 1 and 1.0 behave the same
    assert qs.boolean(1) == qs.boolean(1.0)
    assert qs.boolean(0) == qs.boolean(0.0)
    
    # Test negative zero
    assert qs.boolean(0) == qs.boolean(-0)
    assert qs.boolean(0.0) == qs.boolean(-0.0)
    
    # Test that other numbers fail
    with pytest.raises(ValueError):
        qs.boolean(2)
    with pytest.raises(ValueError):
        qs.boolean(-1)
    with pytest.raises(ValueError):
        qs.boolean(0.5)


def test_boolean_string_whitespace():
    """Test boolean validator with whitespace in strings."""
    # These should fail since the validator checks exact strings
    with pytest.raises(ValueError):
        qs.boolean("true ")
    with pytest.raises(ValueError):
        qs.boolean(" true")
    with pytest.raises(ValueError):
        qs.boolean("True\n")
    with pytest.raises(ValueError):
        qs.boolean("\tfalse")


def test_boolean_case_sensitivity():
    """Test case sensitivity in boolean validator."""
    # Currently accepts "true" and "True" 
    assert qs.boolean("true") == True
    assert qs.boolean("True") == True
    
    # But what about other cases?
    with pytest.raises(ValueError):
        qs.boolean("TRUE")
    with pytest.raises(ValueError):
        qs.boolean("TrUe")
    
    assert qs.boolean("false") == False
    assert qs.boolean("False") == False
    
    with pytest.raises(ValueError):
        qs.boolean("FALSE")
    with pytest.raises(ValueError):
        qs.boolean("FaLsE")


def test_double_special_floats():
    """Test double validator with special float values."""
    # Test infinity
    assert qs.double("inf") == "inf"
    assert qs.double("-inf") == "-inf"
    
    # Test NaN
    assert qs.double("nan") == "nan"
    assert qs.double("NaN") == "NaN"
    
    # These work because Python's float() accepts them
    assert qs.double("Infinity") == "Infinity"
    assert qs.double("-Infinity") == "-Infinity"


def test_double_numeric_formats():
    """Test double validator with various numeric string formats."""
    # Scientific notation
    assert qs.double("1e10") == "1e10"
    assert qs.double("1E10") == "1E10"
    assert qs.double("1.5e-10") == "1.5e-10"
    
    # Leading plus
    assert qs.double("+5") == "+5"
    assert qs.double("+0") == "+0"
    
    # Leading zeros
    assert qs.double("00") == "00"
    assert qs.double("001") == "001"
    assert qs.double("000.5") == "000.5"
    
    # Decimal point variations
    assert qs.double(".5") == ".5"
    assert qs.double("5.") == "5."
    
    # These should fail
    with pytest.raises(ValueError):
        qs.double("1,000")  # Comma separator
    with pytest.raises(ValueError):
        qs.double("1_000")  # Underscore separator


def test_double_with_booleans():
    """Test double validator with boolean inputs."""
    # Python's float() can convert booleans
    assert qs.double(True) == True
    assert qs.double(False) == False
    
    # Verify float conversion works
    assert float(qs.double(True)) == 1.0
    assert float(qs.double(False)) == 0.0


# Test metamorphic property: if double(x) succeeds, then double(double(x)) should also succeed
@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=True, allow_infinity=True),
    st.text(),
    st.booleans()
))
def test_double_idempotent_property(value):
    """Test that if double(x) succeeds, double(double(x)) should also succeed."""
    try:
        result1 = qs.double(value)
        result2 = qs.double(result1)
        # Both should return the same value since double returns input unchanged
        assert result1 == result2 == value
    except ValueError:
        # First call failed, that's fine
        pass


# Test potential confusion between string "0"/"1" and numeric 0/1
def test_boolean_string_vs_numeric():
    """Test that boolean handles string and numeric versions consistently."""
    # String "1" and numeric 1 should both return True
    assert qs.boolean("1") == qs.boolean(1) == True
    
    # String "0" and numeric 0 should both return False  
    assert qs.boolean("0") == qs.boolean(0) == False
    
    # But these are different values that happen to have same boolean result
    assert "1" != 1
    assert "0" != 0


# Test round-trip with validation enabled vs disabled
@given(st.dictionaries(
    st.text(min_size=1, max_size=10),
    st.text(min_size=1, max_size=10),
    min_size=1,
    max_size=3
))
def test_validation_consistency(data):
    """Test that validation doesn't affect round-trip properties."""
    try:
        obj = qs.Spacing.from_dict("Test", data)
        
        # Get dict with validation
        try:
            dict_with_validation = obj.to_dict(validation=True)
        except:
            dict_with_validation = None
            
        # Get dict without validation
        dict_without_validation = obj.to_dict(validation=False)
        
        # If validation succeeds, both should be the same
        if dict_with_validation is not None:
            assert dict_with_validation == dict_without_validation
            
    except (TypeError, KeyError, AttributeError):
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])