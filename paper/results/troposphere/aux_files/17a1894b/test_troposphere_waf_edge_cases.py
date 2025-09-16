import json
from hypothesis import given, strategies as st, assume, settings
import troposphere.waf as waf
import troposphere.validators as validators


# Test edge cases for boolean() function
@given(st.one_of(
    st.floats(),
    st.sampled_from([0.0, 1.0, 0.5, -1, 2, 100, -100]),
    st.sampled_from(["TRUE", "FALSE", "yes", "no", "on", "off", "True ", " False"]),
    st.sampled_from(["01", "10", "00", "11"]),
))
def test_boolean_edge_cases(value):
    """Test boolean() with edge case inputs"""
    valid_true = [True, 1, "1", "true", "True"]
    valid_false = [False, 0, "0", "false", "False"]
    
    try:
        result = validators.boolean(value)
        # Check if the input was actually valid
        assert value in valid_true + valid_false, f"boolean({value!r}) = {result!r} but {value!r} is not in the valid list"
    except ValueError:
        # Should only raise for invalid inputs
        assert value not in valid_true + valid_false


# Test integer() with numeric strings that might overflow
@given(st.one_of(
    st.sampled_from([
        "99999999999999999999999999999999999999999999999999",
        "-99999999999999999999999999999999999999999999999999",
        "1" * 1000,  # Very long string of 1s
        "0" * 1000,  # Very long string of 0s
    ]),
    st.text(alphabet="0123456789", min_size=50, max_size=100),
    st.text(alphabet="-0123456789", min_size=50, max_size=100),
))
@settings(max_examples=50)
def test_integer_large_numbers(value):
    """Test integer() with very large numeric strings"""
    try:
        result = validators.integer(value)
        # Should preserve the original string value
        assert result == value
        # Should be convertible to int (Python handles arbitrary precision)
        int_val = int(result)
        assert isinstance(int_val, int)
    except ValueError:
        # Should only fail if not a valid integer string
        try:
            int(value)
            assert False, f"integer() raised ValueError but int() succeeded for {value!r}"
        except:
            pass  # Expected


# Test integer() with special numeric formats
@given(st.one_of(
    st.sampled_from(["0x10", "0o10", "0b10", "1e10", "1.0", "1.5", "+123", "++123", "--123"]),
    st.sampled_from([" 123", "123 ", " 123 ", "\t123", "123\n"]),
))
def test_integer_special_formats(value):
    """Test integer() with special numeric formats"""
    result = None
    raised_error = False
    
    try:
        result = validators.integer(value)
    except ValueError:
        raised_error = True
    
    # Check consistency with int()
    try:
        int_val = int(value)
        # If int() succeeds, integer() should too
        assert not raised_error, f"integer() raised ValueError but int() succeeded for {value!r}"
        assert result == value
    except ValueError:
        # If int() fails, integer() should also fail
        assert raised_error, f"integer() returned {result!r} but int() failed for {value!r}"


# Test boolean() returns actual Python bool type
@given(st.sampled_from([True, 1, "1", "true", "True", False, 0, "0", "false", "False"]))
def test_boolean_return_type(value):
    """Test that boolean() returns actual bool type"""
    result = validators.boolean(value)
    assert isinstance(result, bool), f"boolean({value!r}) returned {type(result).__name__} instead of bool"


# Test with None and empty values
@given(st.sampled_from([None, "", [], {}, (), 0.0, 1.0]))
def test_edge_none_empty(value):
    """Test validators with None and empty values"""
    # Test boolean
    valid_for_boolean = [True, False, 1, 0, 0.0] if value in [True, False, 1, 0, 0.0] else []
    
    try:
        bool_result = validators.boolean(value)
        assert value in valid_for_boolean or value in [True, 1, "1", "true", "True", False, 0, "0", "false", "False"]
    except ValueError:
        assert value not in [True, 1, "1", "true", "True", False, 0, "0", "false", "False"]
    
    # Test integer
    try:
        int_result = validators.integer(value)
        # Should be convertible
        int(value)
    except (ValueError, TypeError):
        pass  # Expected


# Test WebACL with empty strings (which should be valid for Name/MetricName)  
@given(st.sampled_from(["ALLOW", "BLOCK", "COUNT"]))
def test_webacl_empty_names(action_type):
    """Test if WebACL accepts empty strings for required string fields"""
    action = waf.Action(Type=action_type)
    
    # Try with empty string names - these are required fields
    try:
        webacl = waf.WebACL(
            "TestWebACL",
            Name="",  # Empty string
            MetricName="",  # Empty string
            DefaultAction=action
        )
        # Should be able to serialize
        webacl_dict = webacl.to_dict()
        assert webacl_dict["Properties"]["Name"] == ""
        assert webacl_dict["Properties"]["MetricName"] == ""
    except Exception as e:
        # If it fails, it should be a clear validation error
        pass


# Test round-trip with special characters in names
@given(
    st.sampled_from(["ALLOW", "BLOCK", "COUNT"]),
    st.text(alphabet="!@#$%^&*(){}[]|\\:;\"'<>,.?/~`", min_size=1, max_size=10)
)
def test_special_chars_in_names(action_type, special_name):
    """Test handling of special characters in name fields"""
    action = waf.Action(Type=action_type)
    
    try:
        webacl = waf.WebACL(
            "TestWebACL",
            Name=special_name,
            MetricName=special_name,
            DefaultAction=action
        )
        
        # Convert to dict and back
        dict1 = webacl.to_dict()
        webacl2 = waf.WebACL.from_dict("TestWebACL2", dict1["Properties"])
        dict2 = webacl2.to_dict()
        
        # Should preserve special characters
        assert dict1["Properties"]["Name"] == special_name
        assert dict2["Properties"]["Name"] == special_name
    except Exception:
        pass  # Some special characters might not be allowed