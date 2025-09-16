#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import json
from hypothesis import given, strategies as st, assume, settings
import troposphere.pinpointemail as pe
from troposphere.validators import boolean

# Strategy for valid alphanumeric titles
valid_titles = st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')), min_size=1, max_size=50)

# Strategy for boolean-like values
boolean_values = st.sampled_from([
    True, False, 
    1, 0,
    "true", "false",
    "True", "False",
    "1", "0"
])

# Strategy for invalid boolean values
invalid_boolean_values = st.one_of(
    st.text(min_size=1).filter(lambda x: x not in ["true", "false", "True", "False", "1", "0"]),
    st.integers(min_value=2),
    st.integers(max_value=-1),
    st.floats(),
    st.none(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
)

# Test 1: Boolean validator accepts specific values and rejects others
@given(value=boolean_values)
def test_boolean_validator_accepts_valid_values(value):
    result = boolean(value)
    assert isinstance(result, bool)
    if value in [True, 1, "1", "true", "True"]:
        assert result is True
    else:
        assert result is False

@given(value=invalid_boolean_values)
def test_boolean_validator_rejects_invalid_values(value):
    try:
        boolean(value)
        assert False, f"Expected ValueError for {value}"
    except ValueError:
        pass  # Expected

# Test 2: Title validation - must be alphanumeric
@given(title=valid_titles)
def test_valid_title_accepted(title):
    obj = pe.ConfigurationSet(Name="TestConfig", title=title)
    obj.validate_title()  # Should not raise

@given(title=st.text(min_size=1).filter(lambda x: not x.replace(' ', '').isalnum() or ' ' in x))
def test_invalid_title_rejected(title):
    assume(title != "")  # Empty string handled separately
    assume(not all(c.isalnum() for c in title))  # Must have non-alphanumeric
    try:
        obj = pe.ConfigurationSet(Name="TestConfig", title=title)
        assert False, f"Expected ValueError for title '{title}'"
    except ValueError as e:
        assert "not alphanumeric" in str(e)

# Test 3: Round-trip property for ConfigurationSet
@given(
    title=valid_titles,
    name=st.text(min_size=1, max_size=100),
    sending_enabled=boolean_values,
    reputation_enabled=boolean_values,
    sending_pool=st.one_of(st.none(), st.text(min_size=1, max_size=100)),
    redirect_domain=st.one_of(st.none(), st.text(min_size=1, max_size=100))
)
def test_configuration_set_round_trip(title, name, sending_enabled, reputation_enabled, sending_pool, redirect_domain):
    # Create object with properties
    obj = pe.ConfigurationSet(title=title, Name=name)
    
    # Add optional properties
    if sending_enabled is not None:
        obj.SendingOptions = pe.SendingOptions(SendingEnabled=boolean(sending_enabled))
    if reputation_enabled is not None:
        obj.ReputationOptions = pe.ReputationOptions(ReputationMetricsEnabled=boolean(reputation_enabled))
    if sending_pool is not None:
        obj.DeliveryOptions = pe.DeliveryOptions(SendingPoolName=sending_pool)
    if redirect_domain is not None:
        obj.TrackingOptions = pe.TrackingOptions(CustomRedirectDomain=redirect_domain)
    
    # Convert to dict
    dict_repr = obj.to_dict()
    
    # Create new object from dict
    new_obj = pe.ConfigurationSet.from_dict(title, dict_repr["Properties"])
    
    # They should be equal
    assert obj.to_dict() == new_obj.to_dict()
    assert obj.title == new_obj.title

# Test 4: Required properties validation
@given(title=valid_titles)
def test_required_properties_validation(title):
    # ConfigurationSet requires Name property
    try:
        obj = pe.ConfigurationSet(title=title)  # Missing required Name
        obj.to_dict()  # This should trigger validation
        assert False, "Expected ValueError for missing required property"
    except ValueError as e:
        assert "required" in str(e).lower()

# Test 5: JSON serialization round-trip
@given(
    title=valid_titles,
    name=st.text(min_size=1, max_size=100),
    pool_name=st.one_of(st.none(), st.text(min_size=1, max_size=50))
)
def test_json_serialization_round_trip(title, name, pool_name):
    # Create DedicatedIpPool object
    obj = pe.DedicatedIpPool(title=title)
    if pool_name:
        obj.PoolName = pool_name
    
    # Convert to JSON
    json_str = obj.to_json()
    
    # Parse JSON
    parsed = json.loads(json_str)
    
    # Should be able to reconstruct from parsed dict
    if "Properties" in parsed and parsed["Properties"]:
        new_obj = pe.DedicatedIpPool.from_dict(title, parsed["Properties"])
        assert obj.to_dict() == new_obj.to_dict()

# Test 6: EventDestination with complex nested structure
@given(
    title=valid_titles, 
    config_set_name=st.text(min_size=1, max_size=100),
    event_name=st.text(min_size=1, max_size=100),
    enabled=boolean_values,
    event_types=st.lists(st.sampled_from(["SEND", "BOUNCE", "COMPLAINT", "DELIVERY", "REJECT"]), min_size=1, max_size=5, unique=True),
    topic_arn=st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters=':/-'), min_size=10, max_size=200)
)
def test_event_destination_complex_structure(title, config_set_name, event_name, enabled, event_types, topic_arn):
    # Create complex nested object
    obj = pe.ConfigurationSetEventDestination(
        title=title,
        ConfigurationSetName=config_set_name,
        EventDestinationName=event_name
    )
    
    # Create EventDestination with nested properties
    event_dest = pe.EventDestination(
        Enabled=boolean(enabled),
        MatchingEventTypes=event_types,
        SnsDestination=pe.SnsDestination(TopicArn=topic_arn)
    )
    obj.EventDestination = event_dest
    
    # Test round-trip
    dict_repr = obj.to_dict()
    new_obj = pe.ConfigurationSetEventDestination.from_dict(title, dict_repr["Properties"])
    
    assert obj.to_dict() == new_obj.to_dict()

# Test 7: DimensionConfiguration list handling
@given(
    dimensions=st.lists(
        st.fixed_dictionaries({
            'name': st.text(min_size=1, max_size=50),
            'value': st.text(min_size=1, max_size=50), 
            'source': st.sampled_from(['MESSAGE_TAG', 'EMAIL_HEADER', 'LINK_TAG'])
        }),
        min_size=0,
        max_size=10
    )
)
def test_dimension_configuration_list(dimensions):
    # Create CloudWatchDestination with list of DimensionConfigurations
    cw_dest = pe.CloudWatchDestination()
    if dimensions:
        dim_configs = [
            pe.DimensionConfiguration(
                DimensionName=d['name'],
                DefaultDimensionValue=d['value'],
                DimensionValueSource=d['source']
            )
            for d in dimensions
        ]
        cw_dest.DimensionConfigurations = dim_configs
    
    # Convert to dict and back
    dict_repr = cw_dest.to_dict()
    
    # Verify structure
    if dimensions:
        assert "DimensionConfigurations" in dict_repr
        assert len(dict_repr["DimensionConfigurations"]) == len(dimensions)
        for i, dim in enumerate(dimensions):
            assert dict_repr["DimensionConfigurations"][i]["DimensionName"] == dim['name']

if __name__ == "__main__":
    print("Running property-based tests for troposphere.pinpointemail...")
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])