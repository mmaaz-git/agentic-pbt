#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import troposphere.panorama as panorama
from troposphere import Tags
from troposphere.validators import boolean
import json


# Strategy for generating valid payload data strings
payload_data_strategy = st.text(min_size=0, max_size=1000)

# Strategy for generating property names
name_strategy = st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), min_codepoint=48), min_size=1, max_size=255)

# Strategy for role ARNs
arn_strategy = st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc'), min_codepoint=45), min_size=20, max_size=500).map(lambda s: f"arn:aws:iam::123456789012:role/{s}")

# Strategy for S3 bucket names
bucket_strategy = st.text(alphabet=st.characters(whitelist_categories=('Ll', 'Nd'), whitelist_characters='-'), min_size=3, max_size=63).filter(lambda s: not s.startswith('-') and not s.endswith('-'))

# Strategy for version strings
version_strategy = st.text(alphabet=st.characters(whitelist_categories=('Nd',), whitelist_characters='.-'), min_size=1, max_size=20)


# Test 1: Round-trip property for ManifestPayload
@given(payload_data=payload_data_strategy)
def test_manifest_payload_round_trip(payload_data):
    """Test that ManifestPayload survives to_dict/from_dict round trip"""
    original = panorama.ManifestPayload(PayloadData=payload_data)
    
    # Convert to dict and back
    dict_repr = original.to_dict()
    
    # Create new object from dict (need to extract just the PayloadData part)
    reconstructed = panorama.ManifestPayload.from_dict(None, dict_repr)
    
    # Check they produce the same dict representation
    assert reconstructed.to_dict() == dict_repr


# Test 2: Round-trip property for ApplicationInstance
@given(
    device=name_strategy,
    description=st.one_of(st.none(), name_strategy),
    name=st.one_of(st.none(), name_strategy),
    role_arn=st.one_of(st.none(), arn_strategy),
    manifest_data=payload_data_strategy,
    override_data=st.one_of(st.none(), payload_data_strategy)
)
def test_application_instance_round_trip(device, description, name, role_arn, manifest_data, override_data):
    """Test that ApplicationInstance survives to_dict/from_dict round trip"""
    
    # Build the object with required and optional properties
    kwargs = {
        'DefaultRuntimeContextDevice': device,
        'ManifestPayload': panorama.ManifestPayload(PayloadData=manifest_data)
    }
    
    if description is not None:
        kwargs['Description'] = description
    if name is not None:
        kwargs['Name'] = name
    if role_arn is not None:
        kwargs['RuntimeRoleArn'] = role_arn
    if override_data is not None:
        kwargs['ManifestOverridesPayload'] = panorama.ManifestOverridesPayload(PayloadData=override_data)
    
    original = panorama.ApplicationInstance("TestInstance", **kwargs)
    
    # Convert to dict and extract properties
    dict_repr = original.to_dict()
    properties = dict_repr.get('Properties', {})
    
    # Create new object from properties dict
    reconstructed = panorama.ApplicationInstance.from_dict("TestInstance2", properties)
    
    # Check they produce the same dict representation (except title)
    assert reconstructed.to_dict()['Properties'] == properties


# Test 3: Boolean validator confluence property
@given(st.sampled_from([True, False, 1, 0, "true", "false", "True", "False", "1", "0"]))
def test_boolean_validator_confluence(value):
    """Test that boolean validator is confluent - multiple paths to same result"""
    result = boolean(value)
    
    # The function claims these values map to specific booleans
    expected_true = [True, 1, "1", "true", "True"]
    expected_false = [False, 0, "0", "false", "False"]
    
    if value in expected_true:
        assert result is True
        # Test confluence: all true values should produce the same result
        for other_true_value in expected_true:
            assert boolean(other_true_value) == result
    elif value in expected_false:
        assert result is False
        # Test confluence: all false values should produce the same result
        for other_false_value in expected_false:
            assert boolean(other_false_value) == result


# Test 4: Boolean validator with PackageVersion
@given(
    package_id=name_strategy,
    package_version=version_strategy,
    patch_version=version_strategy,
    mark_latest=st.sampled_from([True, False, 1, 0, "true", "false", "True", "False", "1", "0"])
)
def test_package_version_boolean_property(package_id, package_version, patch_version, mark_latest):
    """Test that PackageVersion correctly handles boolean MarkLatest property"""
    
    pkg = panorama.PackageVersion(
        "TestPkgVersion",
        PackageId=package_id,
        PackageVersion=package_version,
        PatchVersion=patch_version,
        MarkLatest=mark_latest
    )
    
    # Convert to dict
    dict_repr = pkg.to_dict()
    
    # The MarkLatest should be normalized to boolean
    if 'MarkLatest' in dict_repr.get('Properties', {}):
        result = dict_repr['Properties']['MarkLatest']
        # Should be actual Python boolean after normalization
        assert isinstance(result, bool)
        
        # Check it matches what boolean() would return
        assert result == boolean(mark_latest)


# Test 5: StorageLocation with multiple optional properties
@given(
    bucket=st.one_of(st.none(), bucket_strategy),
    binary_prefix=st.one_of(st.none(), name_strategy),
    generated_prefix=st.one_of(st.none(), name_strategy),
    manifest_prefix=st.one_of(st.none(), name_strategy),
    repo_prefix=st.one_of(st.none(), name_strategy)
)
def test_storage_location_optional_properties(bucket, binary_prefix, generated_prefix, manifest_prefix, repo_prefix):
    """Test that StorageLocation handles optional properties correctly"""
    
    kwargs = {}
    if bucket is not None:
        kwargs['Bucket'] = bucket
    if binary_prefix is not None:
        kwargs['BinaryPrefixLocation'] = binary_prefix
    if generated_prefix is not None:
        kwargs['GeneratedPrefixLocation'] = generated_prefix  
    if manifest_prefix is not None:
        kwargs['ManifestPrefixLocation'] = manifest_prefix
    if repo_prefix is not None:
        kwargs['RepoPrefixLocation'] = repo_prefix
    
    storage = panorama.StorageLocation(**kwargs)
    dict_repr = storage.to_dict()
    
    # All provided properties should be in the dict
    for key, value in kwargs.items():
        assert dict_repr[key] == value
    
    # No extra properties should be added
    assert set(dict_repr.keys()) == set(kwargs.keys())


# Test 6: Package with StorageLocation composition
@given(
    package_name=name_strategy,
    bucket=st.one_of(st.none(), bucket_strategy)
)
def test_package_with_storage_location(package_name, bucket):
    """Test that Package correctly composes StorageLocation"""
    
    kwargs = {'PackageName': package_name}
    
    if bucket is not None:
        storage = panorama.StorageLocation(Bucket=bucket)
        kwargs['StorageLocation'] = storage
    
    pkg = panorama.Package("TestPackage", **kwargs)
    dict_repr = pkg.to_dict()
    
    assert dict_repr['Properties']['PackageName'] == package_name
    
    if bucket is not None:
        assert 'StorageLocation' in dict_repr['Properties']
        assert dict_repr['Properties']['StorageLocation']['Bucket'] == bucket


# Test 7: Tags serialization property  
@given(st.dictionaries(
    keys=st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), min_codepoint=48), min_size=1, max_size=128),
    values=st.text(min_size=0, max_size=256),
    min_size=0,
    max_size=50
))
def test_tags_serialization(tag_dict):
    """Test that Tags serialize to expected format"""
    
    tags = Tags(tag_dict)
    dict_repr = tags.to_dict()
    
    # Should be a list of dicts with Key and Value
    assert isinstance(dict_repr, list)
    assert len(dict_repr) == len(tag_dict)
    
    # Check all tags are present
    for item in dict_repr:
        assert 'Key' in item
        assert 'Value' in item
        assert tag_dict[item['Key']] == item['Value']
    
    # Check no duplicate keys
    keys = [item['Key'] for item in dict_repr]
    assert len(keys) == len(set(keys))


# Test 8: Required property validation
@given(device=name_strategy)
def test_required_property_validation(device):
    """Test that required properties are enforced"""
    
    # ApplicationInstance requires DefaultRuntimeContextDevice and ManifestPayload
    # Test missing ManifestPayload
    try:
        app = panorama.ApplicationInstance(
            "TestApp",
            DefaultRuntimeContextDevice=device
        )
        # Should raise error when calling to_dict
        app.to_dict()
        assert False, "Should have raised ValueError for missing ManifestPayload"
    except ValueError as e:
        assert "ManifestPayload" in str(e)
        assert "required" in str(e).lower()
    
    # Test missing DefaultRuntimeContextDevice
    try:
        app = panorama.ApplicationInstance(
            "TestApp",
            ManifestPayload=panorama.ManifestPayload(PayloadData="test")
        )
        app.to_dict()
        assert False, "Should have raised ValueError for missing DefaultRuntimeContextDevice"
    except ValueError as e:
        assert "DefaultRuntimeContextDevice" in str(e)
        assert "required" in str(e).lower()


# Test 9: Invalid boolean values should raise ValueError
@given(st.text().filter(lambda x: x not in ["true", "false", "True", "False", "1", "0"]))
def test_boolean_validator_invalid_values(value):
    """Test that invalid boolean values raise ValueError"""
    assume(value not in [True, False, 1, 0])  # These are valid non-string values
    
    try:
        boolean(value)
        assert False, f"Should have raised ValueError for {repr(value)}"
    except ValueError:
        pass  # Expected


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])