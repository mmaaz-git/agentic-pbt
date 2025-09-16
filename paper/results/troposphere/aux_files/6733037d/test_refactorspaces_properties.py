#!/usr/bin/env python3
import troposphere.refactorspaces as refactorspaces
from hypothesis import given, strategies as st, assume
import pytest

# Test 1: boolean function should always raise ValueError with a message when it fails
@given(st.one_of(
    st.text(),
    st.integers(),
    st.floats(),
    st.booleans(),
    st.none(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_boolean_error_message(value):
    """Test that boolean() either returns a bool or raises ValueError with a message"""
    try:
        result = refactorspaces.boolean(value)
        # If it succeeds, it should return a boolean
        assert isinstance(result, bool)
    except ValueError as e:
        # If it raises ValueError, it should have a meaningful error message
        error_msg = str(e)
        assert error_msg != "", f"ValueError raised with empty message for input: {repr(value)}"
    except Exception as e:
        # Should only raise ValueError, not other exceptions
        pytest.fail(f"Unexpected exception type {type(e).__name__} for input {repr(value)}")

# Test 2: boolean function should handle case variations consistently
@given(st.sampled_from([
    ("true", "True", "TRUE", "tRuE"),
    ("false", "False", "FALSE", "fAlSe")
]))
def test_boolean_case_insensitive(variations):
    """Test that boolean() handles case variations of true/false consistently"""
    results = []
    for variant in variations:
        try:
            result = refactorspaces.boolean(variant)
            results.append(result)
        except ValueError:
            results.append("ERROR")
    
    # All variants should produce the same result
    assert len(set(results)) == 1, f"Inconsistent results for case variations {variations}: {results}"

# Test 3: Test that to_dict doesn't crash for valid objects
@given(
    name=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    description=st.text(max_size=200)
)
def test_environment_to_dict(name, description):
    """Test that Environment.to_dict() works for valid inputs"""
    env = refactorspaces.Environment("TestEnv")
    env.Name = name
    env.Description = description
    
    result = env.to_dict()
    
    # Basic properties of the result
    assert isinstance(result, dict)
    assert "Type" in result
    assert result["Type"] == "AWS::RefactorSpaces::Environment"
    
    # Properties should be included if set
    assert "Properties" in result
    assert result["Properties"]["Name"] == name
    assert result["Properties"]["Description"] == description

# Test 4: Test ApiGatewayProxyInput to_dict doesn't lose data
@given(
    endpoint_type=st.text(min_size=1, max_size=50),
    stage_name=st.text(min_size=1, max_size=50)
)
def test_apigateway_proxy_to_dict(endpoint_type, stage_name):
    """Test that ApiGatewayProxyInput preserves all properties in to_dict()"""
    proxy = refactorspaces.ApiGatewayProxyInput()
    proxy.EndpointType = endpoint_type
    proxy.StageName = stage_name
    
    result = proxy.to_dict()
    
    assert isinstance(result, dict)
    assert result.get("EndpointType") == endpoint_type
    assert result.get("StageName") == stage_name