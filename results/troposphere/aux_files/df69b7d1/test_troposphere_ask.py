"""
Property-based tests for troposphere.ask module
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import json
from hypothesis import given, strategies as st, assume, settings
import troposphere.ask as ask
import troposphere


# Strategy for valid alphanumeric titles
valid_titles = st.text(alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")), min_size=1, max_size=50)

# Strategy for strings
safe_strings = st.text(min_size=1, max_size=100).filter(lambda x: x.strip())

# Strategy for S3 bucket names (AWS has specific rules, but we'll keep it simple)
s3_bucket_names = st.text(alphabet=st.characters(whitelist_categories=("Ll", "Nd"), whitelist_characters="-"), min_size=3, max_size=63).filter(lambda x: not x.startswith('-') and not x.endswith('-'))

# Strategy for S3 keys
s3_keys = st.text(min_size=1, max_size=1024).filter(lambda x: x.strip())


@st.composite
def authentication_config_strategy(draw):
    """Generate valid AuthenticationConfiguration objects"""
    return ask.AuthenticationConfiguration(
        ClientId=draw(safe_strings),
        ClientSecret=draw(safe_strings),
        RefreshToken=draw(safe_strings)
    )


@st.composite
def overrides_strategy(draw):
    """Generate valid Overrides objects"""
    # Manifest should be a dict according to the props
    manifest = draw(st.dictionaries(safe_strings, safe_strings, max_size=5))
    return ask.Overrides(Manifest=manifest)


@st.composite
def skill_package_strategy(draw):
    """Generate valid SkillPackage objects"""
    package = ask.SkillPackage(
        S3Bucket=draw(s3_bucket_names),
        S3Key=draw(s3_keys)
    )
    
    # Optionally add non-required fields
    if draw(st.booleans()):
        package.S3BucketRole = draw(safe_strings)
    if draw(st.booleans()):
        package.S3ObjectVersion = draw(safe_strings)
    if draw(st.booleans()):
        package.Overrides = draw(overrides_strategy())
    
    return package


@st.composite
def skill_strategy(draw):
    """Generate valid Skill objects"""
    title = draw(valid_titles)
    auth = draw(authentication_config_strategy())
    package = draw(skill_package_strategy())
    vendor_id = draw(safe_strings)
    
    return ask.Skill(
        title,
        AuthenticationConfiguration=auth,
        SkillPackage=package,
        VendorId=vendor_id
    )


# Test 1: Round-trip property - from_dict(to_dict(obj)) should equal original object
@given(skill_strategy())
@settings(max_examples=100)
def test_skill_round_trip_property(skill):
    """Test that Skill objects can be serialized and deserialized without loss"""
    # Convert to dict
    skill_dict = skill.to_dict()
    
    # Extract properties for reconstruction
    properties = skill_dict.get('Properties', {})
    
    # Recreate from dict
    reconstructed = ask.Skill.from_dict(skill.title, properties)
    
    # They should be equal
    assert skill == reconstructed, f"Round-trip failed for skill {skill.title}"
    
    # Also check JSON round-trip
    json_str = skill.to_json(validation=False)
    json_dict = json.loads(json_str)
    reconstructed_from_json = ask.Skill.from_dict(skill.title, json_dict.get('Properties', {}))
    assert skill == reconstructed_from_json


@given(authentication_config_strategy())
@settings(max_examples=100)
def test_authentication_config_round_trip(auth_config):
    """Test AuthenticationConfiguration round-trip property"""
    # Create a minimal parent object to test with
    auth_dict = auth_config.to_dict()
    
    # Recreate from dict
    reconstructed = ask.AuthenticationConfiguration._from_dict(**auth_dict)
    
    # Check equality via dict comparison
    assert auth_config.to_dict() == reconstructed.to_dict()


@given(skill_package_strategy())
@settings(max_examples=100)
def test_skill_package_round_trip(package):
    """Test SkillPackage round-trip property"""
    package_dict = package.to_dict()
    
    # Recreate from dict
    reconstructed = ask.SkillPackage._from_dict(**package_dict)
    
    # Check equality
    assert package.to_dict() == reconstructed.to_dict()


# Test 2: Required properties validation
@given(valid_titles, authentication_config_strategy(), safe_strings)
def test_skill_missing_required_properties(title, auth, vendor_id):
    """Test that missing required properties raise errors on validation"""
    # Create skill without SkillPackage (required)
    skill = ask.Skill(title)
    skill.AuthenticationConfiguration = auth
    skill.VendorId = vendor_id
    
    # Should raise error when trying to convert to dict with validation
    try:
        skill.to_dict()
        assert False, "Should have raised ValueError for missing SkillPackage"
    except ValueError as e:
        assert "SkillPackage" in str(e)


# Test 3: Title validation
@given(st.text(min_size=1, max_size=50).filter(lambda x: not x.isalnum()))
def test_invalid_title_characters(invalid_title):
    """Test that non-alphanumeric titles are rejected"""
    assume(invalid_title and not invalid_title.replace('_', '').isalnum())  # Make sure it's truly invalid
    
    try:
        skill = ask.Skill(invalid_title)
        assert False, f"Should have rejected title: {invalid_title}"
    except ValueError as e:
        assert "not alphanumeric" in str(e)


# Test 4: Type validation
@given(valid_titles, st.one_of(st.integers(), st.floats(), st.lists(st.text())))
def test_skill_wrong_type_vendor_id(title, wrong_value):
    """Test that wrong types for VendorId are rejected"""
    auth = ask.AuthenticationConfiguration(
        ClientId="client",
        ClientSecret="secret", 
        RefreshToken="token"
    )
    package = ask.SkillPackage(S3Bucket="bucket", S3Key="key")
    
    try:
        skill = ask.Skill(
            title,
            AuthenticationConfiguration=auth,
            SkillPackage=package,
            VendorId=wrong_value  # Should be string
        )
        # If we get here without error, check if it was coerced
        if not isinstance(skill.VendorId, str):
            assert False, f"VendorId should be string, got {type(skill.VendorId)}"
    except (TypeError, AttributeError):
        pass  # Expected for wrong types


# Test 5: Equality property
@given(skill_strategy())
def test_skill_equality_property(skill):
    """Test that skills with same properties are equal"""
    # Create identical skill
    skill2 = ask.Skill(
        skill.title,
        AuthenticationConfiguration=skill.AuthenticationConfiguration,
        SkillPackage=skill.SkillPackage,
        VendorId=skill.VendorId
    )
    
    assert skill == skill2, "Skills with same properties should be equal"
    
    # Modify one property and check inequality
    skill3 = ask.Skill(
        skill.title,
        AuthenticationConfiguration=skill.AuthenticationConfiguration,
        SkillPackage=skill.SkillPackage,
        VendorId=skill.VendorId + "_modified"
    )
    
    assert skill != skill3, "Skills with different properties should not be equal"


# Test 6: JSON serialization doesn't lose data
@given(skill_strategy())
def test_json_serialization_preserves_data(skill):
    """Test that JSON serialization preserves all data"""
    json_str = skill.to_json(validation=False)
    parsed = json.loads(json_str)
    
    # Check structure
    assert 'Type' in parsed
    assert parsed['Type'] == 'Alexa::ASK::Skill'
    assert 'Properties' in parsed
    
    # Check all required properties are present
    props = parsed['Properties']
    assert 'AuthenticationConfiguration' in props
    assert 'SkillPackage' in props
    assert 'VendorId' in props


# Test 7: Property dict structure validation
@given(authentication_config_strategy())
def test_authentication_config_dict_structure(auth):
    """Test that AuthenticationConfiguration produces correct dict structure"""
    auth_dict = auth.to_dict()
    
    # Should have all required fields
    assert 'ClientId' in auth_dict
    assert 'ClientSecret' in auth_dict
    assert 'RefreshToken' in auth_dict
    
    # Values should be strings
    assert isinstance(auth_dict['ClientId'], str)
    assert isinstance(auth_dict['ClientSecret'], str)
    assert isinstance(auth_dict['RefreshToken'], str)


# Test 8: SkillPackage optional properties
@given(s3_bucket_names, s3_keys, st.one_of(st.none(), safe_strings))
def test_skill_package_optional_properties(bucket, key, optional_version):
    """Test that SkillPackage handles optional properties correctly"""
    package = ask.SkillPackage(S3Bucket=bucket, S3Key=key)
    
    if optional_version is not None:
        package.S3ObjectVersion = optional_version
    
    package_dict = package.to_dict()
    
    # Required fields must be present
    assert 'S3Bucket' in package_dict
    assert 'S3Key' in package_dict
    
    # Optional field should only be present if set
    if optional_version is not None:
        assert 'S3ObjectVersion' in package_dict
        assert package_dict['S3ObjectVersion'] == optional_version
    else:
        assert 'S3ObjectVersion' not in package_dict


# Test 9: Overrides with complex dict
@given(st.dictionaries(
    safe_strings,
    st.recursive(
        st.one_of(safe_strings, st.integers(), st.booleans()),
        lambda children: st.one_of(
            st.lists(children, max_size=3),
            st.dictionaries(safe_strings, children, max_size=3)
        ),
        max_leaves=10
    ),
    max_size=5
))
def test_overrides_with_nested_manifest(manifest):
    """Test that Overrides handles nested manifest dicts correctly"""
    overrides = ask.Overrides(Manifest=manifest)
    overrides_dict = overrides.to_dict()
    
    assert 'Manifest' in overrides_dict
    assert overrides_dict['Manifest'] == manifest
    
    # Test round-trip
    reconstructed = ask.Overrides._from_dict(**overrides_dict)
    assert reconstructed.to_dict() == overrides_dict


# Test 10: Skill with all optional fields
@given(skill_strategy())
def test_skill_with_metadata_and_attributes(skill):
    """Test that Skill handles CloudFormation attributes correctly"""
    # Add CloudFormation-specific attributes
    skill.DependsOn = "SomeOtherResource"
    skill.Condition = "SomeCondition"
    skill.Metadata = {"key": "value"}
    
    skill_dict = skill.to_dict()
    
    # These should be in the resource dict, not in Properties
    assert 'DependsOn' in skill_dict
    assert 'Condition' in skill_dict
    assert 'Metadata' in skill_dict
    assert skill_dict['DependsOn'] == "SomeOtherResource"
    assert skill_dict['Condition'] == "SomeCondition"
    assert skill_dict['Metadata'] == {"key": "value"}


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])