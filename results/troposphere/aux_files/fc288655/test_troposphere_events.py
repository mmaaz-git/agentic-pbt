"""Property-based tests for troposphere.events module"""

import json
from hypothesis import given, strategies as st, assume
import troposphere.events as events


# Test 1: boolean() function properties
@given(st.one_of(
    st.sampled_from([True, 1, "1", "true", "True"]),
    st.sampled_from([False, 0, "0", "false", "False"]),
    st.text(),
    st.integers(),
    st.floats(),
    st.none(),
    st.lists(st.integers())
))
def test_boolean_function(value):
    """Test that boolean() correctly categorizes values as True/False or raises ValueError"""
    true_values = [True, 1, "1", "true", "True"]
    false_values = [False, 0, "0", "false", "False"]
    
    try:
        result = events.boolean(value)
        # If it succeeds, it must return True or False based on documented values
        if value in true_values:
            assert result is True, f"Expected True for {value!r}, got {result}"
        elif value in false_values:
            assert result is False, f"Expected False for {value!r}, got {result}"
        else:
            # Should have raised ValueError for other values
            assert False, f"Expected ValueError for {value!r}, but got {result}"
    except ValueError:
        # ValueError should only be raised for values not in true_values or false_values
        assert value not in true_values and value not in false_values


# Test 2: integer() function properties
@given(st.one_of(
    st.integers(),
    st.floats(),
    st.text(),
    st.none(),
    st.booleans(),
    st.lists(st.integers())
))
def test_integer_function(value):
    """Test that integer() accepts integer-convertible values and rejects others"""
    try:
        result = events.integer(value)
        # If it succeeds, the original value must be convertible to int
        int(value)  # This should also succeed
        # The function should return the original value
        assert result == value
    except ValueError as e:
        # If integer() raises ValueError, int() should also fail
        try:
            int(value)
            # If int() succeeds but integer() failed, that's a bug
            assert False, f"integer() raised ValueError for {value!r} but int() succeeded"
        except (ValueError, TypeError):
            # Both failed, which is correct
            pass


# Test 3: EventBus to_dict serialization property
@given(
    st.text(min_size=1),  # title
    st.text(min_size=1),  # name
    st.one_of(st.none(), st.text()),  # description
    st.one_of(st.none(), st.text())   # kms_key
)
def test_eventbus_to_dict_serialization(title, name, description, kms_key):
    """Test that EventBus.to_dict() always returns a valid dictionary"""
    kwargs = {"Name": name}
    if description is not None:
        kwargs["Description"] = description
    if kms_key is not None:
        kwargs["KmsKeyIdentifier"] = kms_key
    
    eb = events.EventBus(title, **kwargs)
    result = eb.to_dict()
    
    # to_dict() should always return a dictionary
    assert isinstance(result, dict)
    
    # Should have required keys
    assert "Type" in result
    assert result["Type"] == "AWS::Events::EventBus"
    assert "Properties" in result
    assert isinstance(result["Properties"], dict)
    
    # Name should be preserved
    assert result["Properties"]["Name"] == name
    
    # Optional properties should be included only if provided
    if description is not None:
        assert result["Properties"]["Description"] == description
    if kms_key is not None:
        assert result["Properties"]["KmsKeyIdentifier"] == kms_key


# Test 4: EventBus to_json produces valid JSON
@given(
    st.text(min_size=1),  # title
    st.text(min_size=1),  # name
)
def test_eventbus_to_json_validity(title, name):
    """Test that EventBus.to_json() produces valid JSON that can be parsed"""
    eb = events.EventBus(title, Name=name)
    json_str = eb.to_json()
    
    # Should be a string
    assert isinstance(json_str, str)
    
    # Should be valid JSON
    parsed = json.loads(json_str)
    assert isinstance(parsed, dict)
    
    # Should have the same structure as to_dict()
    dict_result = eb.to_dict()
    assert parsed == dict_result


# Test 5: Rule with Target serialization
@given(
    st.text(min_size=1),  # rule title
    st.text(min_size=1),  # rule name
    st.text(min_size=1),  # target id
    st.text(min_size=1),  # target arn
)
def test_rule_with_target_serialization(rule_title, rule_name, target_id, target_arn):
    """Test that Rule with Targets serializes correctly"""
    target = events.Target(
        Id=target_id,
        Arn=target_arn
    )
    
    rule = events.Rule(
        rule_title,
        Name=rule_name,
        Targets=[target]
    )
    
    result = rule.to_dict()
    
    # Check structure
    assert isinstance(result, dict)
    assert result["Type"] == "AWS::Events::Rule"
    assert "Properties" in result
    
    # Check that Targets are serialized
    assert "Targets" in result["Properties"]
    assert isinstance(result["Properties"]["Targets"], list)
    assert len(result["Properties"]["Targets"]) == 1
    
    # Check target properties
    target_dict = result["Properties"]["Targets"][0]
    assert target_dict["Id"] == target_id
    assert target_dict["Arn"] == target_arn


# Test 6: Multiple boolean values in sequence
@given(st.lists(st.one_of(
    st.sampled_from([True, 1, "1", "true", "True", False, 0, "0", "false", "False"]),
), min_size=1, max_size=100))
def test_boolean_consistency(values):
    """Test that boolean() gives consistent results for the same input"""
    results = []
    for value in values:
        result = events.boolean(value)
        results.append(result)
    
    # Check that same input always gives same output
    for i, value in enumerate(values):
        assert events.boolean(value) == results[i]