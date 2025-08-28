import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import json
import re
from hypothesis import given, strategies as st, assume, settings
import troposphere.ecr as ecr
from troposphere import validators
from troposphere.validators.ecr import policytypes
from troposphere.compat import validate_policytype


# Test 1: Boolean validator property
@given(st.one_of(
    st.sampled_from([True, 1, "1", "true", "True"]),
    st.sampled_from([False, 0, "0", "false", "False"])
))
def test_boolean_validator_valid_inputs(value):
    """Boolean validator should convert known values to True/False"""
    result = validators.boolean(value)
    assert result in [True, False]
    if value in [True, 1, "1", "true", "True"]:
        assert result is True
    else:
        assert result is False


@given(st.one_of(
    st.text(min_size=1).filter(lambda x: x not in ["1", "0", "true", "True", "false", "False"]),
    st.integers().filter(lambda x: x not in [0, 1]),
    st.floats(),
    st.none(),
    st.lists(st.integers())
))
def test_boolean_validator_invalid_inputs(value):
    """Boolean validator should raise ValueError for invalid inputs"""
    try:
        result = validators.boolean(value)
        assert False, f"Should have raised ValueError for {value}"
    except ValueError:
        pass


# Test 2: Policy type validation
@given(st.dictionaries(st.text(), st.text()))
def test_policytypes_accepts_dict(policy):
    """policytypes validator should accept dict"""
    result = policytypes(policy)
    assert result == policy


@given(st.one_of(
    st.text(),
    st.integers(),
    st.lists(st.text()),
    st.none()
))
def test_policytypes_rejects_non_dict(policy):
    """policytypes validator should reject non-dict types"""
    if not isinstance(policy, dict):
        try:
            policytypes(policy)
            assert False, f"Should have raised TypeError for {type(policy)}"
        except TypeError as e:
            assert "Invalid policy type" in str(e)


# Test 3: Title validation for AWS resources
@given(st.text(alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")), min_size=1))
def test_valid_resource_titles(title):
    """Resource titles must be alphanumeric"""
    try:
        repo = ecr.Repository(title)
        assert repo.title == title
    except ValueError:
        assert False, f"Valid alphanumeric title '{title}' was rejected"


@given(st.text(min_size=1).filter(lambda x: not re.match(r"^[a-zA-Z0-9]+$", x)))
def test_invalid_resource_titles(title):
    """Non-alphanumeric titles should be rejected"""
    try:
        repo = ecr.Repository(title)
        assert False, f"Invalid title '{title}' was accepted"
    except ValueError as e:
        assert "not alphanumeric" in str(e)


# Test 4: Property type validation
@given(st.booleans())
def test_image_scanning_configuration_boolean_property(value):
    """ImageScanningConfiguration.ScanOnPush should accept boolean values"""
    config = ecr.ImageScanningConfiguration()
    config.ScanOnPush = value
    assert config.ScanOnPush == value


@given(st.one_of(
    st.sampled_from([True, False, 0, 1, "true", "false", "True", "False", "0", "1"])
))
def test_image_scanning_configuration_boolean_coercion(value):
    """ImageScanningConfiguration.ScanOnPush should coerce boolean-like values"""
    config = ecr.ImageScanningConfiguration()
    config.ScanOnPush = value
    expected = validators.boolean(value)
    assert config.ScanOnPush == expected


# Test 5: Repository property setting
@given(
    repo_name=st.text(alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")), min_size=1, max_size=50),
    image_tag_mutability=st.sampled_from(["MUTABLE", "IMMUTABLE"])
)
def test_repository_property_setting(repo_name, image_tag_mutability):
    """Repository properties should be settable with valid values"""
    repo = ecr.Repository("TestRepo")
    repo.RepositoryName = repo_name
    repo.ImageTagMutability = image_tag_mutability
    
    assert repo.RepositoryName == repo_name
    assert repo.ImageTagMutability == image_tag_mutability


# Test 6: EncryptionConfiguration validation
@given(
    encryption_type=st.sampled_from(["AES256", "KMS"]),
    kms_key=st.text(min_size=1, max_size=100)
)
def test_encryption_configuration(encryption_type, kms_key):
    """EncryptionConfiguration should accept valid encryption settings"""
    config = ecr.EncryptionConfiguration()
    config.EncryptionType = encryption_type
    if encryption_type == "KMS":
        config.KmsKey = kms_key
        assert config.KmsKey == kms_key
    assert config.EncryptionType == encryption_type


# Test 7: ReplicationRule destinations
@given(
    regions=st.lists(
        st.sampled_from(["us-east-1", "us-west-2", "eu-west-1", "ap-northeast-1"]),
        min_size=1,
        max_size=3
    ),
    registry_ids=st.lists(st.text(alphabet=st.characters(whitelist_categories=("Nd",)), min_size=12, max_size=12), min_size=1, max_size=3)
)
def test_replication_destinations(regions, registry_ids):
    """ReplicationDestination should handle multiple regions and registry IDs"""
    destinations = []
    for region, registry_id in zip(regions, registry_ids):
        dest = ecr.ReplicationDestination()
        dest.Region = region
        dest.RegistryId = registry_id
        destinations.append(dest)
        assert dest.Region == region
        assert dest.RegistryId == registry_id


# Test 8: to_dict serialization and deserialization
@given(
    repo_name=st.text(alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd", "-")), min_size=1, max_size=50).filter(lambda x: re.match(r"^[a-zA-Z0-9][a-zA-Z0-9-]*$", x)),
    scan_on_push=st.booleans()
)
def test_repository_to_dict_roundtrip(repo_name, scan_on_push):
    """Repository should serialize to dict and maintain properties"""
    repo = ecr.Repository("TestRepo")
    repo.RepositoryName = repo_name
    
    scan_config = ecr.ImageScanningConfiguration()
    scan_config.ScanOnPush = scan_on_push
    repo.ImageScanningConfiguration = scan_config
    
    # Convert to dict
    repo_dict = repo.to_dict()
    
    # Verify structure
    assert "Type" in repo_dict
    assert repo_dict["Type"] == "AWS::ECR::Repository"
    assert "Properties" in repo_dict
    assert "RepositoryName" in repo_dict["Properties"]
    assert repo_dict["Properties"]["RepositoryName"] == repo_name
    
    # Verify nested properties
    if "ImageScanningConfiguration" in repo_dict["Properties"]:
        assert "ScanOnPush" in repo_dict["Properties"]["ImageScanningConfiguration"]
        assert repo_dict["Properties"]["ImageScanningConfiguration"]["ScanOnPush"] == scan_on_push


# Test 9: Repository filter validation
@given(
    filter_text=st.text(min_size=1, max_size=100),
    filter_type=st.sampled_from(["PREFIX_MATCH"])
)
def test_repository_filter(filter_text, filter_type):
    """RepositoryFilter should accept filter and filter type"""
    filter_obj = ecr.RepositoryFilter()
    filter_obj.Filter = filter_text
    filter_obj.FilterType = filter_type
    
    assert filter_obj.Filter == filter_text
    assert filter_obj.FilterType == filter_type


# Test 10: JSON serialization doesn't lose precision or change values
@given(
    st.builds(
        lambda name, desc, arch: {
            "name": name,
            "description": desc if desc else None,
            "architectures": arch
        },
        name=st.text(alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")), min_size=1, max_size=20),
        desc=st.one_of(st.none(), st.text(max_size=100)),
        arch=st.lists(st.sampled_from(["x86_64", "arm64", "i386"]), max_size=3)
    )
)
def test_repository_catalog_data_preserves_values(data):
    """RepositoryCatalogData should preserve values through property setting"""
    catalog = ecr.RepositoryCatalogData()
    
    if data["description"]:
        catalog.RepositoryDescription = data["description"]
        assert catalog.RepositoryDescription == data["description"]
    
    if data["architectures"]:
        catalog.Architectures = data["architectures"]
        assert catalog.Architectures == data["architectures"]