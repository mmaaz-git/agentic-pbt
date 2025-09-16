"""Property-based tests for troposphere.comprehend module"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import json
import string
from hypothesis import given, strategies as st, assume, settings
import pytest

# Import troposphere components
from troposphere import validators, BaseAWSObject, AWSObject, AWSProperty
from troposphere.comprehend import (
    DocumentClassifier, Flywheel, VpcConfig, DataSecurityConfig,
    DocumentClassifierInputDataConfig, DocumentClassifierOutputDataConfig,
    AugmentedManifestsListItem, DocumentClassifierDocuments,
    DocumentReaderConfig, TaskConfig, DocumentClassificationConfig,
    EntityRecognitionConfig, EntityTypesListItem
)


# Test validation functions
@given(st.one_of(
    st.just(True), st.just(1), st.just("1"), st.just("true"), st.just("True"),
    st.just(False), st.just(0), st.just("0"), st.just("false"), st.just("False")
))
def test_boolean_validator_valid_inputs(value):
    """Test that boolean validator handles all documented valid inputs"""
    result = validators.boolean(value)
    assert isinstance(result, bool)
    if value in [True, 1, "1", "true", "True"]:
        assert result is True
    else:
        assert result is False


@given(st.one_of(st.integers(), st.text(string.digits, min_size=1)))
def test_integer_validator_valid_inputs(value):
    """Test that integer validator accepts valid integer inputs"""
    result = validators.integer(value)
    assert result == value
    # Should be convertible to int
    int(result)


@given(st.integers())
def test_positive_integer_validator(value):
    """Test positive_integer validator correctly validates positive integers"""
    if value >= 0:
        result = validators.positive_integer(value)
        assert result == value
    else:
        with pytest.raises(ValueError, match="is not a positive integer"):
            validators.positive_integer(value)


@given(st.integers(), st.integers(), st.integers())
def test_integer_range_validator(min_val, max_val, test_val):
    """Test integer_range validator enforces bounds correctly"""
    assume(min_val <= max_val)  # Ensure valid range
    
    validator = validators.integer_range(min_val, max_val)
    
    if min_val <= test_val <= max_val:
        result = validator(test_val)
        assert result == test_val
    else:
        with pytest.raises(ValueError, match="Integer must be between"):
            validator(test_val)


@given(st.integers(min_value=-100000, max_value=100000))
def test_network_port_validator(port):
    """Test network_port validator enforces valid port range"""
    if -1 <= port <= 65535:
        result = validators.network_port(port)
        assert result == port
    else:
        with pytest.raises(ValueError, match="must been between 0 and 65535"):
            validators.network_port(port)


# S3 bucket name validation
@given(st.text(string.ascii_lowercase + string.digits + ".-", min_size=3, max_size=63))
def test_s3_bucket_name_validator(name):
    """Test s3_bucket_name validator with various inputs"""
    # Filter out invalid patterns
    if ".." in name:
        with pytest.raises(ValueError, match="is not a valid s3 bucket name"):
            validators.s3_bucket_name(name)
        return
    
    # IP address pattern
    import re
    ip_re = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
    if ip_re.match(name):
        with pytest.raises(ValueError, match="is not a valid s3 bucket name"):
            validators.s3_bucket_name(name)
        return
    
    # Valid pattern check
    s3_bucket_name_re = re.compile(r"^[a-z\d][a-z\d\.-]{1,61}[a-z\d]$")
    if s3_bucket_name_re.match(name):
        result = validators.s3_bucket_name(name)
        assert result == name
    else:
        with pytest.raises(ValueError, match="is not a valid s3 bucket name"):
            validators.s3_bucket_name(name)


# Test AWS object title validation
@given(st.text())
def test_aws_object_title_validation(title):
    """Test that AWS objects validate titles correctly"""
    import re
    valid_names = re.compile(r"^[a-zA-Z0-9]+$")
    
    if title and valid_names.match(title):
        # Should succeed
        obj = DocumentClassifier(title, DataAccessRoleArn="arn", 
                                DocumentClassifierName="test",
                                InputDataConfig=DocumentClassifierInputDataConfig(),
                                LanguageCode="en")
        assert obj.title == title
    else:
        # Should fail
        with pytest.raises(ValueError, match='Name ".*" not alphanumeric'):
            DocumentClassifier(title, DataAccessRoleArn="arn",
                             DocumentClassifierName="test", 
                             InputDataConfig=DocumentClassifierInputDataConfig(),
                             LanguageCode="en")


# Test VpcConfig properties
@given(st.lists(st.text(min_size=1), min_size=1), 
       st.lists(st.text(min_size=1), min_size=1))
def test_vpc_config_required_properties(security_groups, subnets):
    """Test VpcConfig enforces required properties"""
    vpc = VpcConfig(SecurityGroupIds=security_groups, Subnets=subnets)
    d = vpc.to_dict()
    assert d["SecurityGroupIds"] == security_groups
    assert d["Subnets"] == subnets


# Test round-trip property for AWS objects
@given(st.text(string.ascii_letters + string.digits, min_size=1, max_size=10))
def test_document_classifier_round_trip(name):
    """Test DocumentClassifier to_dict and from_dict are inverse operations"""
    obj = DocumentClassifier(
        name,
        DataAccessRoleArn="arn:aws:iam::123456789012:role/test",
        DocumentClassifierName="TestClassifier", 
        InputDataConfig=DocumentClassifierInputDataConfig(
            S3Uri="s3://bucket/input"
        ),
        LanguageCode="en"
    )
    
    # Convert to dict
    dict_repr = obj.to_dict()
    
    # Recreate from dict
    properties = dict_repr.get("Properties", {})
    new_obj = DocumentClassifier.from_dict(name, properties)
    
    # They should produce the same dict representation
    assert obj.to_dict() == new_obj.to_dict()


# Test JSON serialization
@given(st.text(string.ascii_letters + string.digits, min_size=1, max_size=10))
def test_flywheel_json_serialization(name):
    """Test that Flywheel objects can be serialized to JSON and parsed back"""
    flywheel = Flywheel(
        name,
        DataAccessRoleArn="arn:aws:iam::123456789012:role/test",
        DataLakeS3Uri="s3://bucket/datalake",
        FlywheelName="TestFlywheel"
    )
    
    # Convert to JSON
    json_str = flywheel.to_json()
    
    # Should be valid JSON
    parsed = json.loads(json_str)
    assert isinstance(parsed, dict)
    assert parsed["Type"] == "AWS::Comprehend::Flywheel"
    assert parsed["Properties"]["FlywheelName"] == "TestFlywheel"


# Test property type validation
@given(st.one_of(st.integers(), st.floats(), st.booleans(), st.none()))
def test_document_classifier_type_validation(value):
    """Test that DocumentClassifier validates property types"""
    with pytest.raises(TypeError):
        # LanguageCode should be a string, not other types
        DocumentClassifier(
            "TestName",
            DataAccessRoleArn="arn",
            DocumentClassifierName="test",
            InputDataConfig=DocumentClassifierInputDataConfig(),
            LanguageCode=value  # This should fail for non-strings
        )


# Test list property validation
@given(st.one_of(st.text(), st.integers(), st.dictionaries(st.text(), st.text())))
def test_vpc_config_list_validation(value):
    """Test that VpcConfig validates list properties"""
    if not isinstance(value, list):
        with pytest.raises(TypeError):
            VpcConfig(SecurityGroupIds=value, Subnets=["subnet-1"])


# Test optional vs required properties
def test_document_classifier_required_properties():
    """Test that DocumentClassifier enforces required properties"""
    # Missing required properties should fail validation
    obj = DocumentClassifier("Test")
    with pytest.raises(ValueError, match="Resource .* required in type"):
        obj.to_dict()  # This triggers validation


# Test AugmentedManifestsListItem properties
@given(st.lists(st.text(min_size=1), min_size=1), st.text(min_size=1))
def test_augmented_manifests_list_item(attr_names, s3_uri):
    """Test AugmentedManifestsListItem with required properties"""
    item = AugmentedManifestsListItem(
        AttributeNames=attr_names,
        S3Uri=s3_uri
    )
    d = item.to_dict()
    assert d["AttributeNames"] == attr_names
    assert d["S3Uri"] == s3_uri


# Test EntityTypesListItem
@given(st.text(min_size=1))
def test_entity_types_list_item(entity_type):
    """Test EntityTypesListItem type property"""
    item = EntityTypesListItem(Type=entity_type)
    d = item.to_dict()
    assert d["Type"] == entity_type


# Test mode validation in DocumentClassificationConfig
@given(st.text())
def test_document_classification_config_mode(mode):
    """Test DocumentClassificationConfig mode property"""
    config = DocumentClassificationConfig(Mode=mode)
    d = config.to_dict()
    assert d["Mode"] == mode


# Test complex nested structure
@given(st.text(string.ascii_letters + string.digits, min_size=1, max_size=10))
def test_complex_nested_structure(name):
    """Test complex nested AWS object structures serialize correctly"""
    vpc_config = VpcConfig(
        SecurityGroupIds=["sg-1", "sg-2"],
        Subnets=["subnet-1", "subnet-2"]
    )
    
    data_security = DataSecurityConfig(
        VolumeKmsKeyId="key-123",
        VpcConfig=vpc_config
    )
    
    flywheel = Flywheel(
        name,
        DataAccessRoleArn="arn:aws:iam::123456789012:role/test",
        DataLakeS3Uri="s3://bucket/datalake",
        FlywheelName="TestFlywheel",
        DataSecurityConfig=data_security
    )
    
    d = flywheel.to_dict()
    
    # Check nested structure is preserved
    assert d["Properties"]["DataSecurityConfig"]["VpcConfig"]["SecurityGroupIds"] == ["sg-1", "sg-2"]
    assert d["Properties"]["DataSecurityConfig"]["VolumeKmsKeyId"] == "key-123"