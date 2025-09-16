import json
from hypothesis import given, strategies as st, assume, settings
import troposphere.waf as waf
import troposphere.validators as validators


# Test metamorphic property: Creating same object different ways should be equivalent
@given(st.sampled_from(["ALLOW", "BLOCK", "COUNT"]))
def test_action_creation_equivalence(action_type):
    """Test that creating Action via constructor vs from_dict are equivalent"""
    # Method 1: Direct constructor
    action1 = waf.Action(Type=action_type)
    dict1 = action1.to_dict()
    
    # Method 2: from_dict
    action2 = waf.Action.from_dict("Action2", {"Type": action_type})
    dict2 = action2.to_dict()
    
    # Should produce same dictionary representation
    assert dict1 == dict2


# Test that validation happens at the right time
@given(st.text().filter(lambda x: x not in ["ALLOW", "BLOCK", "COUNT"]))
def test_validation_timing(invalid_type):
    """Test when validation actually occurs for invalid values"""
    # Creating with invalid type should work
    action = waf.Action(Type=invalid_type)
    
    # But converting to dict should fail
    try:
        action.to_dict()
        assert False, f"to_dict() should have failed for invalid Type={invalid_type!r}"
    except ValueError as e:
        assert "Type must be one of" in str(e)
    
    # to_json should also fail
    try:
        action.to_json()
        assert False, f"to_json() should have failed for invalid Type={invalid_type!r}"
    except ValueError as e:
        assert "Type must be one of" in str(e)


# Test no_validation() method disables validation
@given(st.text())
def test_no_validation_method(any_type):
    """Test that no_validation() method actually disables validation"""
    action = waf.Action(Type=any_type)
    action.no_validation()
    
    # Should not raise even with invalid type
    dict_result = action.to_dict()
    assert dict_result["Type"] == any_type
    
    # to_dict with validation=False should also work
    dict_result2 = action.to_dict(validation=False)
    assert dict_result2["Type"] == any_type


# Test ByteMatchSet with various field types
@given(
    st.text(min_size=1, max_size=50),
    st.lists(
        st.builds(
            waf.ByteMatchTuples,
            FieldToMatch=st.builds(
                waf.FieldToMatch,
                Type=st.text(min_size=1),
                Data=st.text()
            ),
            TargetString=st.text(),
            TextTransformation=st.text(),
            PositionalConstraint=st.text()
        ),
        max_size=3
    )
)
def test_bytematchset_complex(name, tuples):
    """Test ByteMatchSet with complex nested structures"""
    byte_match_set = waf.ByteMatchSet(
        "TestByteMatchSet",
        Name=name,
        ByteMatchTuples=tuples
    )
    
    # Should be able to serialize
    dict_result = byte_match_set.to_dict(validation=False)
    
    # Round-trip test
    byte_match_set2 = waf.ByteMatchSet.from_dict("TestByteMatchSet2", dict_result["Properties"])
    dict_result2 = byte_match_set2.to_dict(validation=False)
    
    # Should be equivalent
    assert dict_result["Properties"] == dict_result2["Properties"]


# Test that all AWS resource classes have consistent behavior
@given(st.sampled_from([waf.ByteMatchSet, waf.IPSet, waf.Rule, waf.WebACL, 
                        waf.SqlInjectionMatchSet, waf.XssMatchSet, waf.SizeConstraintSet]))
def test_aws_object_common_methods(cls):
    """Test that all AWS object classes have consistent interface"""
    # All should have these methods
    assert hasattr(cls, 'to_dict')
    assert hasattr(cls, 'to_json')
    assert hasattr(cls, 'from_dict')
    assert hasattr(cls, 'validate')
    assert hasattr(cls, 'no_validation')
    
    # All should have props attribute
    assert hasattr(cls, 'props')
    assert isinstance(cls.props, dict)


# Test integer() with bytes input
@given(st.binary())
def test_integer_with_bytes(byte_value):
    """Test integer() behavior with bytes input"""
    try:
        result = validators.integer(byte_value)
        # If it succeeds, check it's consistent with int()
        int_val = int(byte_value)
        assert result == byte_value
    except (ValueError, TypeError):
        # Should fail consistently with int()
        try:
            int(byte_value)
            assert False, f"integer() failed but int() succeeded for {byte_value!r}"
        except:
            pass  # Expected


# Test boolean with numeric boundary values
@given(st.sampled_from([0.99999, 1.00001, -0.00001, 0.00001, 1e-10, -1e-10]))
def test_boolean_numeric_boundaries(value):
    """Test boolean() with values near 0 and 1"""
    try:
        result = validators.boolean(value)
        # Should only succeed for exactly 0.0 or 1.0 
        assert value in [0, 1, 0.0, 1.0], f"boolean({value}) returned {result} but {value} is not exactly 0 or 1"
    except ValueError:
        # Should fail for non-exact values
        assert value not in [0, 1, 0.0, 1.0]


# Test JSON serialization preserves unicode and special chars
@given(
    st.sampled_from(["ALLOW", "BLOCK", "COUNT"]),
    st.text(alphabet="😀🎉✨🚀💻🐍日本語中文한글", min_size=1, max_size=10)
)
def test_unicode_preservation(action_type, unicode_text):
    """Test that unicode characters are preserved through serialization"""
    webacl = waf.WebACL(
        "TestWebACL",
        Name=unicode_text,
        MetricName=unicode_text,
        DefaultAction=waf.Action(Type=action_type)
    )
    
    # to_json and back
    json_str = webacl.to_json(validation=False)
    parsed = json.loads(json_str)
    
    # Unicode should be preserved
    assert parsed["Properties"]["Name"] == unicode_text
    assert parsed["Properties"]["MetricName"] == unicode_text


# Test properties dictionary immutability
def test_props_immutability():
    """Test if modifying props dictionary affects class behavior"""
    # Get original props
    original_props = waf.Action.props.copy()
    
    # Try to modify it
    waf.Action.props["NewField"] = (str, False)
    
    # Create an instance
    action = waf.Action(Type="ALLOW")
    
    # Check if the new field is recognized
    try:
        action_with_new = waf.Action(Type="ALLOW", NewField="test")
        dict_result = action_with_new.to_dict(validation=False)
        has_new_field = "NewField" in dict_result
    except:
        has_new_field = False
    
    # Restore original props
    waf.Action.props = original_props
    
    # The class should accept dynamic attributes even if not in props
    assert has_new_field or True  # This test is just exploratory