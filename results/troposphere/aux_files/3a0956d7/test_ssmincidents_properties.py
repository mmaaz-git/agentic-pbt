import math
from hypothesis import given, strategies as st, assume, settings
import troposphere.ssmincidents as ssmincidents
import pytest


@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(alphabet='0123456789', min_size=1),
    st.text(alphabet='0123456789 ', min_size=1).filter(lambda x: x.strip()),
    st.booleans()
))
def test_integer_function_type_preservation(value):
    """Test that integer() function should either convert to int or reject"""
    try:
        result = ssmincidents.integer(value)
        
        # If it accepts a string representation of an integer, 
        # it should convert it to actual integer type
        if isinstance(value, str) and value.strip().isdigit():
            # BUG: Returns string instead of integer
            assert isinstance(result, int), f"integer('{value}') returned {type(result).__name__} instead of int"
            
        # If it accepts numeric types, should preserve or convert to int
        elif isinstance(value, (int, float, bool)):
            # For valid integer-like values, should return as int or original type
            if isinstance(value, float) and value.is_integer():
                # Floats that are whole numbers could reasonably become ints
                assert isinstance(result, (int, float))
            else:
                # Other numeric types can stay as-is or become int
                assert isinstance(result, (int, float, bool))
    except (ValueError, OverflowError):
        # It's OK to reject invalid inputs
        pass


@given(st.text())
def test_boolean_function_case_insensitivity(text):
    """Test that boolean() function should handle case-insensitive true/false"""
    
    # Only test variations of true/false
    if text.lower() not in ['true', 'false']:
        return
        
    try:
        # Try the original text
        result1 = ssmincidents.boolean(text)
        
        # All case variations should work the same way
        for variant in [text.upper(), text.lower(), text.capitalize()]:
            try:
                result2 = ssmincidents.boolean(variant)
                assert result2 == result1, f"boolean('{text}') != boolean('{variant}')"
            except ValueError:
                # BUG: Case sensitivity - some variants fail while others pass
                pytest.fail(f"boolean('{variant}') failed but boolean('{text}') succeeded")
                
    except ValueError:
        # If original fails, all variants should fail
        for variant in [text.upper(), text.lower(), text.capitalize()]:
            try:
                ssmincidents.boolean(variant)
                # BUG: Inconsistent case handling
                pytest.fail(f"boolean('{text}') failed but boolean('{variant}') succeeded")
            except ValueError:
                pass  # Expected


@given(
    st.text(min_size=1),
    st.lists(st.text())
)
def test_validation_completeness(key, values):
    """Test that validation either happens at construction or to_dict, not both"""
    
    # Create object - should either validate now or defer
    construction_failed = False
    try:
        obj = ssmincidents.SsmParameter(Key=key, Values=values)
    except TypeError as e:
        construction_failed = True
        # If construction validates types, it should be consistent
        return
        
    # If construction succeeded, to_dict should also succeed or fail consistently
    try:
        result = obj.to_dict()
        assert result['Key'] == key
        assert result['Values'] == values
    except (TypeError, ValueError) as e:
        # If validation was deferred to to_dict, that's OK
        # But if construction succeeded without type checking, that's concerning
        if not construction_failed:
            # This is actually expected behavior - validation happens at to_dict
            pass


@given(
    st.integers(min_value=1, max_value=5),
    st.text(min_size=1, max_size=20)
)  
def test_incident_template_impact_integer_handling(impact, title):
    """Test that Impact field properly handles integer validation"""
    
    # Test with actual integer
    template1 = ssmincidents.IncidentTemplate(Title=title, Impact=impact)
    dict1 = template1.to_dict()
    assert 'Impact' in dict1
    assert isinstance(dict1['Impact'], int)
    
    # Test with string representation
    impact_str = str(impact)
    template2 = ssmincidents.IncidentTemplate(Title=title, Impact=impact_str)
    dict2 = template2.to_dict()
    
    # The integer function should handle this conversion properly
    # Both should result in the same integer value
    assert dict1['Impact'] == dict2['Impact'], f"Impact={impact} != Impact='{impact_str}' after conversion"
    assert isinstance(dict2['Impact'], type(dict1['Impact'])), f"Type mismatch: {type(dict2['Impact'])} vs {type(dict1['Impact'])}"


@given(st.lists(st.one_of(st.text(), st.integers())))
def test_values_list_type_checking(values):
    """Test that Values field properly validates list element types"""
    
    # Values should be a list of strings
    has_non_string = any(not isinstance(v, str) for v in values)
    
    try:
        param = ssmincidents.SsmParameter(Key='test', Values=values)
        result = param.to_dict()
        
        # If it succeeded, all values should have been strings
        if has_non_string:
            pytest.fail(f"SsmParameter accepted non-string values: {values}")
            
    except TypeError as e:
        # Should fail if there are non-string values
        if not has_non_string:
            pytest.fail(f"SsmParameter rejected valid string list: {values}")


@given(
    st.text(min_size=1),
    st.text(min_size=1),
    st.text(min_size=1)
)
def test_nested_object_validation(name, secret_id, service_id):
    """Test that nested required fields are validated"""
    
    # Create nested structure  
    try:
        # Missing required PagerDutyIncidentConfiguration
        config1 = ssmincidents.PagerDutyConfiguration(
            Name=name,
            SecretId=secret_id
            # Missing: PagerDutyIncidentConfiguration
        )
        
        # This should fail when converting to dict
        try:
            result = config1.to_dict()
            pytest.fail("PagerDutyConfiguration.to_dict() succeeded without required PagerDutyIncidentConfiguration")
        except ValueError:
            pass  # Expected
            
    except Exception as e:
        # Construction might validate immediately
        pass
        
    # Test with complete structure
    config2 = ssmincidents.PagerDutyConfiguration(
        Name=name,
        SecretId=secret_id,
        PagerDutyIncidentConfiguration=ssmincidents.PagerDutyIncidentConfiguration(
            ServiceId=service_id
        )
    )
    result2 = config2.to_dict()
    assert result2['Name'] == name
    assert result2['SecretId'] == secret_id
    assert result2['PagerDutyIncidentConfiguration']['ServiceId'] == service_id