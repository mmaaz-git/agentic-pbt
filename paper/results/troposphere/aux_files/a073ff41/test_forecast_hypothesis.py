#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages/')

import json
from hypothesis import given, strategies as st, assume, settings
import troposphere.forecast as forecast

# Strategy for valid alphanumeric titles (required by troposphere)
valid_titles = st.text(alphabet=st.characters(min_codepoint=65, max_codepoint=122, blacklist_characters=r"[\]^_`"), min_size=1, max_size=50).filter(lambda x: x.replace("A", "").replace("Z", "").replace("a", "").replace("z", "").isalnum() if x else False)

# Strategy for AWS ARNs
arns = st.text(min_size=1).map(lambda x: f"arn:aws:forecast:us-east-1:123456789012:{x}")

# Strategy for domain values (from AWS Forecast documentation)
domains = st.sampled_from(["RETAIL", "CUSTOM", "INVENTORY_PLANNING", "EC2_CAPACITY", "WORK_FORCE", "WEB_TRAFFIC", "METRICS"])

# Strategy for dataset types
dataset_types = st.sampled_from(["TARGET_TIME_SERIES", "RELATED_TIME_SERIES", "ITEM_METADATA"])

# Strategy for attribute types
attribute_types = st.sampled_from(["string", "integer", "float", "timestamp"])

# Strategy for data frequency patterns
data_frequencies = st.sampled_from(["Y", "M", "W", "D", "H", "30min", "15min", "10min", "5min", "1min"])

@st.composite
def attributes_items(draw):
    """Generate valid AttributesItems"""
    return forecast.AttributesItems(
        AttributeName=draw(st.text(min_size=1, max_size=50)),
        AttributeType=draw(attribute_types)
    )

@st.composite
def schemas(draw):
    """Generate valid Schema objects"""
    attrs = draw(st.lists(attributes_items(), min_size=1, max_size=10))
    return forecast.Schema(Attributes=attrs)

@st.composite
def encryption_configs(draw):
    """Generate valid EncryptionConfig objects"""
    return forecast.EncryptionConfig(
        KmsKeyArn=draw(arns),
        RoleArn=draw(arns)
    )

@st.composite
def tags_items(draw):
    """Generate valid TagsItems"""
    return forecast.TagsItems(
        Key=draw(st.text(min_size=1, max_size=50)),
        Value=draw(st.text(min_size=1, max_size=50))
    )

@st.composite
def datasets(draw):
    """Generate valid Dataset objects"""
    title = draw(valid_titles)
    dataset_name = draw(st.text(min_size=1, max_size=50))
    dataset_type = draw(dataset_types)
    domain = draw(domains)
    schema = draw(schemas())
    
    kwargs = {
        "DatasetName": dataset_name,
        "DatasetType": dataset_type,
        "Domain": domain,
        "Schema": schema
    }
    
    # Optional fields
    if draw(st.booleans()):
        kwargs["DataFrequency"] = draw(data_frequencies)
    if draw(st.booleans()):
        kwargs["EncryptionConfig"] = draw(encryption_configs())
    if draw(st.booleans()):
        kwargs["Tags"] = draw(st.lists(tags_items(), min_size=1, max_size=5))
    
    return forecast.Dataset(title, **kwargs)

@st.composite
def dataset_groups(draw):
    """Generate valid DatasetGroup objects"""
    title = draw(valid_titles)
    group_name = draw(st.text(min_size=1, max_size=50))
    domain = draw(domains)
    
    kwargs = {
        "DatasetGroupName": group_name,
        "Domain": domain
    }
    
    # Optional fields
    if draw(st.booleans()):
        kwargs["DatasetArns"] = draw(st.lists(arns, min_size=1, max_size=5))
    
    # Note: Tags for DatasetGroup uses the base Tags type, not TagsItems
    
    return forecast.DatasetGroup(title, **kwargs)


# Property 1: Round-trip property for Dataset
@given(datasets())
@settings(max_examples=100)
def test_dataset_round_trip(dataset):
    """Test that Dataset survives to_dict -> from_dict round-trip"""
    # Convert to dict
    dict1 = dataset.to_dict()
    
    # Extract properties for from_dict
    properties = dict1.get("Properties", {})
    
    # Create from dict
    dataset2 = forecast.Dataset.from_dict(dataset.title, properties)
    
    # Convert back to dict
    dict2 = dataset2.to_dict()
    
    # Should be identical
    assert dict1 == dict2, f"Round-trip failed: {dict1} != {dict2}"


# Property 2: Round-trip property for DatasetGroup
@given(dataset_groups())
@settings(max_examples=100)
def test_dataset_group_round_trip(dataset_group):
    """Test that DatasetGroup survives to_dict -> from_dict round-trip"""
    # Convert to dict
    dict1 = dataset_group.to_dict()
    
    # Extract properties for from_dict
    properties = dict1.get("Properties", {})
    
    # Create from dict
    dataset_group2 = forecast.DatasetGroup.from_dict(dataset_group.title, properties)
    
    # Convert back to dict
    dict2 = dataset_group2.to_dict()
    
    # Should be identical
    assert dict1 == dict2, f"Round-trip failed: {dict1} != {dict2}"


# Property 3: JSON serialization round-trip
@given(datasets())
@settings(max_examples=100)
def test_dataset_json_round_trip(dataset):
    """Test that Dataset survives JSON serialization round-trip"""
    # Convert to JSON
    json_str1 = dataset.to_json()
    
    # Parse JSON
    parsed = json.loads(json_str1)
    
    # Should be valid JSON
    assert isinstance(parsed, dict)
    
    # Create from parsed
    properties = parsed.get("Properties", {})
    dataset2 = forecast.Dataset.from_dict(dataset.title, properties)
    
    # Convert back to JSON
    json_str2 = dataset2.to_json()
    
    # Should be identical
    assert json_str1 == json_str2


# Property 4: Equality and hashing invariants
@given(datasets())
@settings(max_examples=100)
def test_dataset_equality_invariants(dataset):
    """Test equality and hashing invariants for Dataset"""
    # Create identical dataset
    dict_repr = dataset.to_dict()
    properties = dict_repr.get("Properties", {})
    dataset2 = forecast.Dataset.from_dict(dataset.title, properties)
    
    # Equality invariants
    assert dataset == dataset2, "Identical datasets should be equal"
    assert not (dataset != dataset2), "Identical datasets should not be not-equal"
    assert hash(dataset) == hash(dataset2), "Equal objects must have equal hashes"
    
    # Reflexivity
    assert dataset == dataset, "Object should equal itself"
    
    # Hash stability
    hash1 = hash(dataset)
    hash2 = hash(dataset)
    assert hash1 == hash2, "Hash should be stable"


# Property 5: to_dict idempotence
@given(datasets())
@settings(max_examples=100)
def test_dataset_to_dict_idempotent(dataset):
    """Test that to_dict is idempotent"""
    dict1 = dataset.to_dict()
    dict2 = dataset.to_dict()
    dict3 = dataset.to_dict()
    
    assert dict1 == dict2 == dict3, "to_dict should be idempotent"


# Property 6: to_json idempotence  
@given(datasets())
@settings(max_examples=100)
def test_dataset_to_json_idempotent(dataset):
    """Test that to_json is idempotent"""
    json1 = dataset.to_json()
    json2 = dataset.to_json()
    json3 = dataset.to_json()
    
    assert json1 == json2 == json3, "to_json should be idempotent"


# Property 7: Validation for required fields
@given(valid_titles, st.text(min_size=1), domains, schemas())
def test_dataset_missing_required_field_validation(title, dataset_name, domain, schema):
    """Test that validation catches missing required fields"""
    # Try creating dataset with missing required field
    incomplete_datasets = [
        # Missing DatasetName
        lambda: forecast.Dataset(title, DatasetType="TARGET_TIME_SERIES", Domain=domain, Schema=schema),
        # Missing DatasetType
        lambda: forecast.Dataset(title, DatasetName=dataset_name, Domain=domain, Schema=schema),
        # Missing Domain
        lambda: forecast.Dataset(title, DatasetName=dataset_name, DatasetType="TARGET_TIME_SERIES", Schema=schema),
        # Missing Schema
        lambda: forecast.Dataset(title, DatasetName=dataset_name, DatasetType="TARGET_TIME_SERIES", Domain=domain),
    ]
    
    for create_incomplete in incomplete_datasets:
        dataset = create_incomplete()
        try:
            # Validation happens on to_dict()
            dataset.to_dict()
            # If we get here, validation failed to catch missing field
            assert False, f"Validation should have caught missing required field"
        except ValueError:
            # Expected - validation caught the missing field
            pass


# Property 8: AttributesItems round-trip
@given(attributes_items())
@settings(max_examples=100)
def test_attributes_items_round_trip(attr):
    """Test AttributesItems to_dict produces correct structure"""
    dict_repr = attr.to_dict()
    
    # Should have the expected keys
    assert "AttributeName" in dict_repr
    assert "AttributeType" in dict_repr
    
    # Values should match
    assert dict_repr["AttributeName"] == attr.AttributeName
    assert dict_repr["AttributeType"] == attr.AttributeType


# Property 9: Schema with Attributes list preservation
@given(schemas())
@settings(max_examples=100)
def test_schema_attributes_preservation(schema):
    """Test that Schema preserves its Attributes list correctly"""
    dict_repr = schema.to_dict()
    
    # Should have Attributes key
    assert "Attributes" in dict_repr
    assert isinstance(dict_repr["Attributes"], list)
    
    # Each attribute should be a dict
    for attr in dict_repr["Attributes"]:
        assert isinstance(attr, dict)
        assert "AttributeName" in attr
        assert "AttributeType" in attr


# Property 10: Dataset with all optional fields
@given(
    valid_titles,
    st.text(min_size=1, max_size=50),
    dataset_types,
    domains,
    schemas(),
    data_frequencies,
    encryption_configs(),
    st.lists(tags_items(), min_size=1, max_size=3)
)
@settings(max_examples=50)
def test_dataset_with_all_fields(title, name, dtype, domain, schema, freq, encryption, tags):
    """Test Dataset with all optional fields populated"""
    dataset = forecast.Dataset(
        title,
        DatasetName=name,
        DatasetType=dtype,
        Domain=domain,
        Schema=schema,
        DataFrequency=freq,
        EncryptionConfig=encryption,
        Tags=tags
    )
    
    dict_repr = dataset.to_dict()
    props = dict_repr["Properties"]
    
    # All fields should be present
    assert props["DatasetName"] == name
    assert props["DatasetType"] == dtype
    assert props["Domain"] == domain
    assert props["DataFrequency"] == freq
    assert "Schema" in props
    assert "EncryptionConfig" in props
    assert "Tags" in props
    
    # Round-trip should work
    dataset2 = forecast.Dataset.from_dict(title, props)
    assert dataset.to_dict() == dataset2.to_dict()


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])