import json
import yaml
from hypothesis import given, strategies as st, assume, settings
import troposphere.validators.ssm as ssm_validators
import troposphere.ssm as ssm
import re


# Strategy for generating valid JSON-serializable data
json_data = st.recursive(
    st.one_of(
        st.none(),
        st.booleans(),
        st.integers(min_value=-1e10, max_value=1e10),
        st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10),
        st.text(min_size=0, max_size=100),
    ),
    lambda children: st.one_of(
        st.lists(children, max_size=10),
        st.dictionaries(st.text(min_size=1, max_size=20), children, max_size=10)
    ),
    max_leaves=50
)


@given(json_data)
@settings(max_examples=500)
def test_validate_document_content_dict_passthrough(data):
    """Test that dicts are returned as-is by validate_document_content"""
    if isinstance(data, dict):
        result = ssm_validators.validate_document_content(data)
        assert result is data  # Should return the exact same object


@given(json_data)
@settings(max_examples=500)
def test_validate_document_content_json_round_trip(data):
    """Test that JSON serialization and validation preserves data"""
    # Convert to JSON string
    json_str = json.dumps(data)
    
    # Validate the JSON string
    result = ssm_validators.validate_document_content(json_str)
    
    # Result should be the same JSON string
    assert result == json_str
    
    # And it should parse back to the original data
    parsed = json.loads(result)
    assert parsed == data


@given(json_data)
@settings(max_examples=500)
def test_validate_document_content_yaml_round_trip(data):
    """Test that YAML serialization and validation preserves data"""
    # Convert to YAML string
    yaml_str = yaml.safe_dump(data)
    
    # Validate the YAML string
    result = ssm_validators.validate_document_content(yaml_str)
    
    # Result should be the same YAML string
    assert result == yaml_str
    
    # And it should parse back to the original data
    parsed = yaml.safe_load(result)
    assert parsed == data


@given(json_data)
@settings(max_examples=500)
def test_json_checker_dict_to_string(data):
    """Test that json_checker converts dicts to JSON strings correctly"""
    if isinstance(data, dict):
        result = ssm_validators.json_checker(data)
        # Should return a JSON string
        assert isinstance(result, str)
        # And it should parse back to the original dict
        parsed = json.loads(result)
        assert parsed == data


@given(json_data)
@settings(max_examples=500)
def test_json_checker_string_validation(data):
    """Test that json_checker validates JSON strings correctly"""
    json_str = json.dumps(data)
    result = ssm_validators.json_checker(json_str)
    # Should return the same string
    assert result == json_str
    # And it should be valid JSON
    parsed = json.loads(result)
    assert parsed == data


# Strategy for S3 bucket names
s3_bucket_name_chars = st.text(
    alphabet="abcdefghijklmnopqrstuvwxyz0123456789.-",
    min_size=3,
    max_size=63
)


@given(s3_bucket_name_chars)
@settings(max_examples=500)
def test_s3_bucket_name_consecutive_periods(name):
    """Test that S3 bucket names with consecutive periods are rejected"""
    if ".." in name:
        try:
            ssm_validators.s3_bucket_name(name)
            assert False, f"Should have rejected name with consecutive periods: {name}"
        except ValueError as e:
            assert "is not a valid s3 bucket name" in str(e)


@given(st.integers(min_value=0, max_value=255),
       st.integers(min_value=0, max_value=255),
       st.integers(min_value=0, max_value=255),
       st.integers(min_value=0, max_value=255))
@settings(max_examples=500)
def test_s3_bucket_name_ip_address(a, b, c, d):
    """Test that IP addresses are rejected as S3 bucket names"""
    ip_address = f"{a}.{b}.{c}.{d}"
    try:
        ssm_validators.s3_bucket_name(ip_address)
        assert False, f"Should have rejected IP address: {ip_address}"
    except ValueError as e:
        assert "is not a valid s3 bucket name" in str(e)


@given(
    st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789", min_size=1, max_size=1),
    st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789.-", min_size=0, max_size=59),
    st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789", min_size=1, max_size=1)
)
@settings(max_examples=500)
def test_s3_bucket_name_valid_names(first, middle, last):
    """Test that valid S3 bucket names are accepted"""
    # Construct a bucket name
    name = first + middle + last
    
    # Remove any accidental consecutive dots
    while ".." in name:
        name = name.replace("..", ".")
    
    # Ensure length is valid (3-63 chars)
    if len(name) < 3 or len(name) > 63:
        return  # Skip this test case
    
    # Check if it matches IP address pattern
    ip_pattern = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
    
    # Check if it follows S3 bucket name pattern
    s3_pattern = re.compile(r"^[a-z\d][a-z\d\.-]{1,61}[a-z\d]$")
    
    if not ip_pattern.match(name) and s3_pattern.match(name):
        # This should be a valid bucket name
        result = ssm_validators.s3_bucket_name(name)
        assert result == name


# Test for Document content property integration
@given(json_data)
@settings(max_examples=200)
def test_document_content_property_integration(data):
    """Test that Document.Content property validation works with various inputs"""
    doc = ssm.Document("TestDoc")
    
    # Test with dict
    if isinstance(data, dict):
        doc.Content = data
        assert doc.Content == data
    
    # Test with JSON string
    json_str = json.dumps(data)
    doc.Content = json_str
    assert doc.Content == json_str
    
    # Test with YAML string
    yaml_str = yaml.safe_dump(data)
    doc.Content = yaml_str
    assert doc.Content == yaml_str