import math
from hypothesis import assume, given, strategies as st, settings
import troposphere.ram as ram
import pytest


@given(st.one_of(
    st.just(True),
    st.just(False),
    st.just(1),
    st.just(0),
    st.just("1"),
    st.just("0"),
    st.just("true"),
    st.just("false"),
    st.just("True"),
    st.just("False")
))
def test_boolean_idempotence(x):
    """boolean(boolean(x)) should equal boolean(x) for valid inputs"""
    result1 = ram.boolean(x)
    result2 = ram.boolean(result1)
    assert result1 == result2
    assert isinstance(result2, bool)


@given(st.one_of(
    st.just("true"),
    st.just("True"),
    st.just("false"),
    st.just("False")
))
def test_boolean_case_sensitivity(s):
    """boolean should handle case variations consistently"""
    lower_result = ram.boolean(s.lower())
    original_result = ram.boolean(s)
    
    # Both should return the same boolean value
    assert lower_result == original_result
    assert isinstance(lower_result, bool)


@given(st.text())
def test_boolean_invalid_strings(s):
    """Test that invalid strings raise ValueError"""
    valid_strings = {"true", "false", "True", "False", "1", "0"}
    if s not in valid_strings:
        with pytest.raises(ValueError):
            ram.boolean(s)


@given(st.integers())
def test_boolean_integer_handling(n):
    """Test integer handling - only 0 and 1 should be valid"""
    if n in [0, 1]:
        result = ram.boolean(n)
        assert isinstance(result, bool)
        assert result == (n == 1)
    else:
        with pytest.raises(ValueError):
            ram.boolean(n)


@given(st.one_of(
    st.none(),
    st.floats(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.text())
))
def test_boolean_type_errors(x):
    """Test that non-supported types raise ValueError"""
    # The function doesn't explicitly check types but will fail the equality checks
    with pytest.raises(ValueError):
        ram.boolean(x)


@given(st.text())
def test_validate_title_alphanumeric(title):
    """Test that validate_title only accepts alphanumeric titles"""
    perm = ram.Permission(title)
    
    # Check if title is alphanumeric (letters, numbers, no special chars except maybe underscore/dash)
    # Based on the error message, it seems to expect alphanumeric
    import re
    # Common AWS naming pattern
    is_valid = bool(re.match(r'^[a-zA-Z0-9]+$', title)) if title else False
    
    if is_valid:
        # Should not raise
        try:
            perm.validate_title()
        except ValueError:
            # If it raises for a seemingly valid alphanumeric, that's a bug
            pytest.fail(f"validate_title raised for alphanumeric title: {title}")
    else:
        # Should raise ValueError
        with pytest.raises(ValueError, match="not alphanumeric"):
            perm.validate_title()


@given(st.text())
def test_permission_name_property(name):
    """Test Permission Name property assignment and retrieval"""
    perm = ram.Permission("TestPerm")
    perm.Name = name
    assert perm.Name == name
    
    # to_dict should include the Name
    d = perm.to_dict()
    if hasattr(perm, 'ResourceType') and perm.ResourceType and hasattr(perm, 'PolicyTemplate') and perm.PolicyTemplate:
        assert 'Properties' in d
        assert d['Properties']['Name'] == name


@given(st.booleans())
def test_resource_share_allow_external_principals(allow):
    """Test ResourceShare AllowExternalPrincipals with boolean values"""
    rs = ram.ResourceShare("TestShare")
    rs.Name = "MyShare"
    
    # The prop uses the boolean function, so it should accept bool values
    rs.AllowExternalPrincipals = allow
    assert rs.AllowExternalPrincipals == allow
    
    # Check it's in the dict
    d = rs.to_dict()
    assert 'Properties' in d
    assert d['Properties']['AllowExternalPrincipals'] == allow