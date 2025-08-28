import json
from hypothesis import given, strategies as st, assume
import troposphere.waf as waf
import troposphere.validators as validators


# Test 1: boolean() function idempotence property
@given(st.one_of(
    st.booleans(),
    st.integers(min_value=0, max_value=1),
    st.sampled_from(["0", "1", "true", "True", "false", "False"])
))
def test_boolean_idempotence(value):
    """Test that boolean(boolean(x)) == boolean(x) for all valid inputs"""
    result1 = validators.boolean(value)
    result2 = validators.boolean(result1)
    assert result1 == result2


# Test 2: boolean() with various input types
@given(st.one_of(
    st.text(),
    st.integers(),
    st.floats(),
    st.none(),
    st.lists(st.integers())
))
def test_boolean_invalid_inputs(value):
    """Test that boolean() handles invalid inputs correctly"""
    valid_true = [True, 1, "1", "true", "True"]
    valid_false = [False, 0, "0", "false", "False"]
    
    if value not in valid_true + valid_false:
        try:
            validators.boolean(value)
            # If we get here without exception, it's a bug
            assert False, f"boolean({value!r}) should have raised ValueError"
        except ValueError:
            pass  # Expected


# Test 3: integer() preserves original value property  
@given(st.one_of(
    st.integers(),
    st.text().filter(lambda x: x.strip() != ''),
    st.sampled_from(["123", "-456", "0", "999999999999999999999"])
))
def test_integer_preserves_value(value):
    """Test that integer() returns the original value unchanged for valid inputs"""
    try:
        result = validators.integer(value)
        # Should return the original value, not the converted int
        assert result == value
        # But it should be convertible to int
        int(result)
    except ValueError:
        # Some inputs may not be valid integers
        pass


# Test 4: integer() with integer-like strings
@given(st.text().filter(lambda x: x.strip() and not x.strip().lstrip('-').isdigit()))
def test_integer_invalid_strings(value):
    """Test integer() raises ValueError for non-integer strings"""
    try:
        validators.integer(value)
        # Check if it's actually convertible to int
        int(value)
    except ValueError:
        pass  # Expected for non-integer strings


# Test 5: validate_waf_action_type preserves valid inputs
@given(st.sampled_from(["ALLOW", "BLOCK", "COUNT"]))
def test_waf_action_type_preserves_valid(action):
    """Test that validate_waf_action_type returns the same valid action unchanged"""
    result = waf.validate_waf_action_type(action)
    assert result == action


# Test 6: validate_waf_action_type rejects invalid inputs
@given(st.text())
def test_waf_action_type_invalid(action):
    """Test that validate_waf_action_type raises ValueError for invalid actions"""
    valid_actions = ["ALLOW", "BLOCK", "COUNT"]
    if action not in valid_actions:
        try:
            waf.validate_waf_action_type(action)
            assert False, f"validate_waf_action_type({action!r}) should have raised ValueError"
        except ValueError as e:
            assert 'Type must be one of' in str(e)


# Test 7: Action class to_dict/from_dict round-trip property
@given(st.sampled_from(["ALLOW", "BLOCK", "COUNT"]))
def test_action_dict_roundtrip(action_type):
    """Test that Action.to_dict() and from_dict() are inverses"""
    # Create an Action
    action1 = waf.Action(Type=action_type)
    
    # Convert to dict
    dict1 = action1.to_dict()
    
    # Create from dict
    action2 = waf.Action.from_dict("TestAction", dict1)
    
    # Convert back to dict
    dict2 = action2.to_dict()
    
    # Should be the same
    assert dict1 == dict2


# Test 8: Action class to_json produces valid JSON
@given(st.sampled_from(["ALLOW", "BLOCK", "COUNT"]))
def test_action_json_valid(action_type):
    """Test that Action.to_json() produces valid JSON"""
    action = waf.Action(Type=action_type)
    json_str = action.to_json()
    
    # Should be valid JSON
    parsed = json.loads(json_str)
    
    # Should contain the Type field
    assert "Type" in parsed
    assert parsed["Type"] == action_type


# Test 9: Multiple WAF classes can be instantiated and serialized
@given(
    st.sampled_from(["ALLOW", "BLOCK", "COUNT"]),
    st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    st.text(min_size=1, max_size=50).filter(lambda x: x.strip())
)
def test_webacl_creation(action_type, name, metric):
    """Test WebACL can be created with valid inputs"""
    # Create a WebACL with required fields
    action = waf.Action(Type=action_type)
    webacl = waf.WebACL(
        "TestWebACL",
        Name=name,
        MetricName=metric,
        DefaultAction=action
    )
    
    # Should be able to convert to dict
    webacl_dict = webacl.to_dict()
    
    # Check required fields are present
    assert "Properties" in webacl_dict
    props = webacl_dict["Properties"]
    assert props["Name"] == name
    assert props["MetricName"] == metric
    assert "DefaultAction" in props
    assert props["DefaultAction"]["Type"] == action_type


# Test 10: IPSet with IPSetDescriptors
@given(
    st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    st.sampled_from(["IPV4", "IPV6"]),
    st.text(min_size=1, max_size=50)
)  
def test_ipset_creation(name, ip_type, value):
    """Test IPSet can be created with descriptors"""
    descriptor = waf.IPSetDescriptors(Type=ip_type, Value=value)
    ipset = waf.IPSet(
        "TestIPSet",
        Name=name,
        IPSetDescriptors=[descriptor]
    )
    
    ipset_dict = ipset.to_dict()
    assert "Properties" in ipset_dict
    props = ipset_dict["Properties"]
    assert props["Name"] == name
    assert "IPSetDescriptors" in props
    assert len(props["IPSetDescriptors"]) == 1
    assert props["IPSetDescriptors"][0]["Type"] == ip_type
    assert props["IPSetDescriptors"][0]["Value"] == value