import datetime
import json
from hypothesis import given, strategies as st, assume, settings
from hypothesis.strategies import composite
import pytest
from azure.mgmt.appconfiguration.models import (
    ConfigurationStore,
    ApiKey,
    ApiKeyListResult,
    CheckNameAvailabilityParameters,
    ConfigurationStoreListResult,
    ConfigurationStoreUpdateParameters,
    Sku,
    ResourceIdentity,
    TrackedResource,
    KeyValue,
    KeyValueFilter,
)
from azure.mgmt.appconfiguration._utils.serialization import (
    RawDeserializer,
    Model,
    attribute_transformer,
    full_restapi_key_transformer,
    last_restapi_key_transformer,
)


# Strategy for generating valid SKU names
sku_names = st.sampled_from(["Free", "Standard", "Premium"])

# Strategy for generating valid locations  
locations = st.sampled_from(["eastus", "westus", "northeurope", "westeurope", "japaneast", "australiaeast"])

# Strategy for generating valid tags
tags_strategy = st.dictionaries(
    keys=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "-", "_"))),
    values=st.text(min_size=0, max_size=256),
    max_size=50
)

# Strategy for generating Sku objects
@composite
def sku_strategy(draw):
    return Sku(name=draw(sku_names))

# Test 1: Model equality consistency - __eq__ and __ne__ should be consistent
@given(
    location1=locations,
    location2=locations,
    sku1=sku_strategy(),
    sku2=sku_strategy(),
    tags1=tags_strategy,
    tags2=tags_strategy,
)
def test_model_equality_consistency(location1, location2, sku1, sku2, tags1, tags2):
    """Test that model __eq__ and __ne__ are consistent opposites"""
    # Create two identical models
    model1 = ConfigurationStore(location=location1, sku=sku1, tags=tags1)
    model2 = ConfigurationStore(location=location1, sku=sku1, tags=tags1)
    
    # Identical models should be equal
    assert model1 == model2
    assert not (model1 != model2)
    
    # Different models
    model3 = ConfigurationStore(location=location2, sku=sku2, tags=tags2)
    
    # If models are equal, they should not be not-equal and vice versa
    if model1 == model3:
        assert not (model1 != model3)
    else:
        assert model1 != model3
    
    # Test reflexivity: x == x should always be true
    assert model1 == model1
    assert not (model1 != model1)


# Test 2: Model serialization round-trip
@given(
    location=locations,
    sku=sku_strategy(),
    tags=tags_strategy,
    disable_local_auth=st.booleans(),
    soft_delete_retention_in_days=st.integers(min_value=1, max_value=90),
    enable_purge_protection=st.booleans(),
)
def test_model_serialization_roundtrip(location, sku, tags, disable_local_auth, soft_delete_retention_in_days, enable_purge_protection):
    """Test that models can be serialized and maintain their properties"""
    model = ConfigurationStore(
        location=location,
        sku=sku,
        tags=tags,
        disable_local_auth=disable_local_auth,
        soft_delete_retention_in_days=soft_delete_retention_in_days,
        enable_purge_protection=enable_purge_protection
    )
    
    # Serialize the model
    serialized = model.serialize()
    
    # Check that serialized form contains expected fields
    assert serialized["location"] == location
    assert serialized["sku"]["name"] == sku.name
    if tags:
        assert serialized.get("tags") == tags
    assert serialized["properties"]["disableLocalAuth"] == disable_local_auth
    assert serialized["properties"]["softDeleteRetentionInDays"] == soft_delete_retention_in_days
    assert serialized["properties"]["enablePurgeProtection"] == enable_purge_protection


# Test 3: Default value application
@given(
    location=locations,
    sku=sku_strategy(),
)
def test_default_value_application(location, sku):
    """Test that default values are applied correctly in ConfigurationStore"""
    # Create model without specifying optional parameters
    model = ConfigurationStore(location=location, sku=sku)
    
    # Check default values are applied
    assert model.disable_local_auth == False  # Default is False
    assert model.soft_delete_retention_in_days == 7  # Default is 7
    assert model.enable_purge_protection == False  # Default is False
    
    # Verify defaults appear in serialization
    serialized = model.serialize()
    assert serialized["properties"]["disableLocalAuth"] == False
    assert serialized["properties"]["softDeleteRetentionInDays"] == 7
    assert serialized["properties"]["enablePurgeProtection"] == False


# Test 4: RawDeserializer JSON handling
@given(
    data=st.one_of(
        st.dictionaries(st.text(), st.text()),
        st.lists(st.integers()),
        st.text(),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.booleans(),
        st.none(),
    )
)
def test_raw_deserializer_json_roundtrip(data):
    """Test that RawDeserializer correctly handles JSON data"""
    # Serialize to JSON string
    json_str = json.dumps(data)
    
    # Deserialize using RawDeserializer
    deserialized = RawDeserializer.deserialize_from_text(json_str, "application/json")
    
    # Should get back the same data
    assert deserialized == data


# Test 5: RawDeserializer content type handling
@given(
    text_data=st.text(min_size=1),
)
def test_raw_deserializer_text_content_type(text_data):
    """Test that RawDeserializer correctly handles text content types"""
    # Test text/plain
    result = RawDeserializer.deserialize_from_text(text_data, "text/plain")
    assert result == text_data
    
    # Test text/html
    result = RawDeserializer.deserialize_from_text(text_data, "text/html")
    assert result == text_data
    
    # Test with no content type - should return data as-is
    result = RawDeserializer.deserialize_from_text(text_data, None)
    assert result == text_data


# Test 6: CheckNameAvailabilityParameters required fields
@given(
    name=st.text(min_size=1, max_size=50),
)
def test_check_name_availability_required_fields(name):
    """Test that CheckNameAvailabilityParameters enforces required fields"""
    # This should work - both required fields provided
    params = CheckNameAvailabilityParameters(
        name=name,
        type="Microsoft.AppConfiguration/configurationStores"
    )
    assert params.name == name
    assert params.type == "Microsoft.AppConfiguration/configurationStores"
    
    # Serialize should include both fields
    serialized = params.serialize()
    assert serialized["name"] == name
    assert serialized["type"] == "Microsoft.AppConfiguration/configurationStores"


# Test 7: ApiKeyListResult with lists
@given(
    next_link=st.one_of(st.none(), st.text(min_size=1)),
    num_keys=st.integers(min_value=0, max_value=10),
)
def test_api_key_list_result(next_link, num_keys):
    """Test ApiKeyListResult list handling"""
    # Create list of ApiKey objects (they're readonly so just empty)
    keys = [ApiKey() for _ in range(num_keys)]
    
    result = ApiKeyListResult(value=keys, next_link=next_link)
    
    # Check properties
    assert result.value == keys
    assert len(result.value) == num_keys
    assert result.next_link == next_link
    
    # Serialize
    serialized = result.serialize()
    if keys:
        assert len(serialized["value"]) == num_keys
    if next_link:
        assert serialized["nextLink"] == next_link


# Test 8: Model additional properties handling
@given(
    location=locations,
    sku=sku_strategy(),
    extra_key=st.text(min_size=1, max_size=20),
    extra_value=st.text(),
)
def test_model_additional_properties_ignored(location, sku, extra_key, extra_value):
    """Test that unknown properties are handled correctly in models"""
    # Try to create model with unknown property
    # This should not raise an error but should log a warning
    kwargs = {
        "location": location,
        "sku": sku,
        extra_key: extra_value,  # Unknown property
    }
    
    model = ConfigurationStore(**kwargs)
    
    # Model should be created successfully with known properties
    assert model.location == location
    assert model.sku == sku
    
    # Unknown property should not be set as attribute
    assert not hasattr(model, extra_key)


# Test 9: Key transformer functions
@given(
    key=st.text(min_size=1, max_size=20),
    value=st.text(),
)
def test_attribute_transformer(key, value):
    """Test attribute_transformer returns correct tuple"""
    attr_desc = {"key": "test_key", "type": "str"}
    result = attribute_transformer(key, attr_desc, value)
    assert result == (key, value)
    assert isinstance(result, tuple)
    assert len(result) == 2


# Test 10: Full RestAPI key transformer with nested keys
@given(
    value=st.text(),
)
def test_full_restapi_key_transformer(value):
    """Test full_restapi_key_transformer with different key patterns"""
    # Test simple key
    attr_desc = {"key": "simpleKey", "type": "str"}
    keys, val = full_restapi_key_transformer("test", attr_desc, value)
    assert keys == ["simpleKey"]
    assert val == value
    
    # Test nested key with dots
    attr_desc = {"key": "properties.nestedKey", "type": "str"}
    keys, val = full_restapi_key_transformer("test", attr_desc, value)
    assert keys == ["properties", "nestedKey"]
    assert val == value
    
    # Test deeply nested
    attr_desc = {"key": "a.b.c.d", "type": "str"}
    keys, val = full_restapi_key_transformer("test", attr_desc, value)
    assert keys == ["a", "b", "c", "d"]
    assert val == value


# Test 11: Last RestAPI key transformer
@given(
    value=st.text(),
)
def test_last_restapi_key_transformer(value):
    """Test last_restapi_key_transformer returns only the last key"""
    # Test simple key
    attr_desc = {"key": "simpleKey", "type": "str"}
    key, val = last_restapi_key_transformer("test", attr_desc, value)
    assert key == "simpleKey"
    assert val == value
    
    # Test nested key - should return only last part
    attr_desc = {"key": "properties.nestedKey", "type": "str"}
    key, val = last_restapi_key_transformer("test", attr_desc, value)
    assert key == "nestedKey"
    assert val == value
    
    # Test deeply nested - should return only last part
    attr_desc = {"key": "a.b.c.d", "type": "str"}
    key, val = last_restapi_key_transformer("test", attr_desc, value)
    assert key == "d"
    assert val == value


# Test 12: ConfigurationStoreUpdateParameters with optional fields
@given(
    tags=st.one_of(st.none(), tags_strategy),
    disable_local_auth=st.one_of(st.none(), st.booleans()),
    enable_purge_protection=st.one_of(st.none(), st.booleans()),
)
def test_configuration_store_update_parameters_optional_fields(tags, disable_local_auth, enable_purge_protection):
    """Test ConfigurationStoreUpdateParameters handles optional fields correctly"""
    params = ConfigurationStoreUpdateParameters(
        tags=tags,
        disable_local_auth=disable_local_auth,
        enable_purge_protection=enable_purge_protection,
    )
    
    # Check properties are set correctly
    assert params.tags == tags
    assert params.disable_local_auth == disable_local_auth
    assert params.enable_purge_protection == enable_purge_protection
    
    # Serialize and check structure
    serialized = params.serialize()
    
    # Only non-None values should be in serialized output
    if tags is not None:
        assert "tags" in serialized
        assert serialized["tags"] == tags
    else:
        assert "tags" not in serialized or serialized["tags"] is None
        
    properties = serialized.get("properties", {})
    if disable_local_auth is not None:
        assert properties.get("disableLocalAuth") == disable_local_auth
    if enable_purge_protection is not None:
        assert properties.get("enablePurgeProtection") == enable_purge_protection


if __name__ == "__main__":
    # Run all tests with pytest
    pytest.main([__file__, "-v"])