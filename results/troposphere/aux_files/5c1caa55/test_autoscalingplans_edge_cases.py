"""Edge case property-based tests for troposphere.autoscalingplans module"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, example
import pytest
from troposphere.autoscalingplans import (
    TagFilter, ApplicationSource, MetricDimension,
    CustomizedLoadMetricSpecification, ScalingInstruction,
    ScalingPlan, TargetTrackingConfiguration
)
from troposphere.validators.autoscalingplans import (
    validate_predictivescalingmaxcapacitybehavior,
    validate_predictivescalingmode,
    validate_scalingpolicyupdatebehavior,
    scalable_dimension_type,
    service_namespace_type,
    statistic_type,
)


# Test non-string inputs to validators
@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.lists(st.text()),
    st.dictionaries(st.text(), st.text())
))
def test_validators_with_non_string_types(value):
    """Validators should handle non-string types appropriately"""
    # These should either raise ValueError or TypeError/AttributeError
    with pytest.raises((ValueError, TypeError, AttributeError)):
        validate_predictivescalingmode(value)
    with pytest.raises((ValueError, TypeError, AttributeError)):
        service_namespace_type(value)
    with pytest.raises((ValueError, TypeError, AttributeError)):
        statistic_type(value)


# Test Unicode and special characters
@given(st.text(alphabet=st.characters(categories=["Sm", "Sc", "Sk", "So"]), min_size=1))
@settings(max_examples=50)
def test_validators_with_unicode_symbols(value):
    """Validators should reject Unicode symbols"""
    with pytest.raises(ValueError):
        validate_predictivescalingmode(value)
    with pytest.raises(ValueError):
        service_namespace_type(value)


# Test whitespace handling  
@given(st.sampled_from([
    " ForecastAndScale",
    "ForecastAndScale ",
    " ForecastAndScale ",
    "\tForecastAndScale",
    "ForecastAndScale\n",
    "Forecast AndScale",
    "Forecast\tAndScale"
]))
def test_validators_whitespace_sensitivity(value):
    """Validators should be sensitive to whitespace"""
    with pytest.raises(ValueError):
        validate_predictivescalingmode(value)


# Test class instantiation with edge case values
@given(
    key=st.text(min_size=0, max_size=1000),
    values=st.lists(st.text(min_size=0, max_size=1000), min_size=0, max_size=10)
)
@settings(max_examples=100)
def test_tagfilter_instantiation(key, values):
    """TagFilter should handle various string inputs"""
    # Should not crash with any string input
    tf = TagFilter(Key=key)
    assert tf.properties.get("Key") == key
    
    if values:
        tf2 = TagFilter(Key=key, Values=values)
        assert tf2.properties.get("Values") == values


# Test MetricDimension with edge cases
@given(
    name=st.text(min_size=0, max_size=1000),
    value=st.text(min_size=0, max_size=1000)
)
@settings(max_examples=100)
def test_metricdimension_instantiation(name, value):
    """MetricDimension should handle various string inputs"""
    md = MetricDimension(Name=name, Value=value)
    assert md.properties.get("Name") == name
    assert md.properties.get("Value") == value


# Test required vs optional field behavior
def test_required_fields_enforcement():
    """Classes should enforce required fields"""
    # TagFilter requires Key
    with pytest.raises((TypeError, KeyError)):
        TagFilter()
    
    # MetricDimension requires Name and Value
    with pytest.raises((TypeError, KeyError)):
        MetricDimension()
    with pytest.raises((TypeError, KeyError)):
        MetricDimension(Name="test")
    with pytest.raises((TypeError, KeyError)):
        MetricDimension(Value="test")


# Test validator substring matching edge case
@given(st.text(min_size=1).filter(lambda x: "ForecastAndScale" in x and x != "ForecastAndScale"))
@settings(max_examples=50)
def test_validator_no_substring_matching(value):
    """Validators should not accept substrings or superstrings of valid values"""
    with pytest.raises(ValueError):
        validate_predictivescalingmode(value)


# Test extremely long invalid strings
@given(st.text(min_size=10000, max_size=100000))
@settings(max_examples=10)
def test_validators_with_very_long_strings(value):
    """Validators should handle very long strings without crashing"""
    assume("ForecastAndScale" != value and "ForecastOnly" != value)
    with pytest.raises(ValueError):
        validate_predictivescalingmode(value)


# Test class property assignment after instantiation
def test_property_modification_after_instantiation():
    """Test if properties can be modified after instantiation"""
    tf = TagFilter(Key="initial")
    assert tf.properties["Key"] == "initial"
    
    # Try to modify - this should work as properties is a regular dict
    tf.properties["Key"] = "modified"
    assert tf.properties["Key"] == "modified"
    
    # Try to add new property
    tf.properties["NewProp"] = "value"
    assert tf.properties["NewProp"] == "value"


# Test TargetTrackingConfiguration with boundary values
@given(
    target_value=st.one_of(
        st.floats(min_value=-1e308, max_value=-1e-10),  # negative
        st.floats(min_value=1e-10, max_value=1e308),    # positive
        st.just(0.0),                                     # zero
    ),
    disable_scale_in=st.booleans(),
    cooldown=st.integers(min_value=-1000, max_value=1000000)
)
@settings(max_examples=100)
def test_targettracking_numeric_properties(target_value, disable_scale_in, cooldown):
    """TargetTrackingConfiguration should handle various numeric inputs"""
    ttc = TargetTrackingConfiguration(
        TargetValue=target_value,
        DisableScaleIn=disable_scale_in,
        ScaleInCooldown=cooldown
    )
    assert ttc.properties["TargetValue"] == target_value
    assert ttc.properties["DisableScaleIn"] == disable_scale_in
    assert ttc.properties["ScaleInCooldown"] == cooldown


# Test ScalingInstruction capacity constraints
@given(
    min_capacity=st.integers(),
    max_capacity=st.integers()
)
@settings(max_examples=100)
def test_scaling_instruction_capacity_values(min_capacity, max_capacity):
    """ScalingInstruction should accept any integer capacity values"""
    # The class itself doesn't validate min < max, it just stores values
    si = ScalingInstruction(
        MinCapacity=min_capacity,
        MaxCapacity=max_capacity,
        ResourceId="test",
        ScalableDimension="ecs:service:DesiredCount",
        ServiceNamespace="ecs",
        TargetTrackingConfigurations=[]
    )
    assert si.properties["MinCapacity"] == min_capacity
    assert si.properties["MaxCapacity"] == max_capacity