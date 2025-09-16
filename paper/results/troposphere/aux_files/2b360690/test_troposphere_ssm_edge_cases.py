import json
import yaml
from hypothesis import given, strategies as st, assume, settings, example
import troposphere.validators.ssm as ssm_validators
import troposphere.ssm as ssm
import re


# Test edge cases in validate_document_content

@given(st.text())
@settings(max_examples=500)
def test_validate_document_content_malformed_json(text):
    """Test that malformed JSON/YAML strings are properly rejected"""
    # Skip if it's actually valid JSON or YAML
    try:
        json.loads(text)
        return  # It's valid JSON, skip
    except:
        pass
    
    try:
        yaml.safe_load(text)
        return  # It's valid YAML, skip
    except:
        pass
    
    # This should raise an error
    try:
        result = ssm_validators.validate_document_content(text)
        assert False, f"Should have rejected malformed JSON/YAML: {text!r}"
    except ValueError as e:
        assert "Content must be one of dict or json/yaml string" in str(e)


@given(st.one_of(st.none(), st.integers(), st.floats(), st.lists(st.integers())))
def test_validate_document_content_invalid_types(value):
    """Test that non-dict, non-string types are rejected"""
    if isinstance(value, dict):
        return  # Skip dicts, they're valid
    
    try:
        result = ssm_validators.validate_document_content(value)
        assert False, f"Should have rejected non-dict/non-string type: {type(value)}"
    except (ValueError, TypeError) as e:
        # Should raise an error for invalid types
        pass


# Test edge cases in json_checker

@given(st.one_of(st.integers(), st.floats(), st.lists(st.integers()), st.none()))
def test_json_checker_invalid_types(value):
    """Test that json_checker properly rejects invalid types"""
    if isinstance(value, (str, dict)):
        return  # Skip valid types
    
    try:
        result = ssm_validators.json_checker(value)
        # AWSHelperFn is allowed, but we're not testing that
        if not hasattr(value, '__class__') or 'AWSHelperFn' not in str(value.__class__):
            assert False, f"Should have rejected type: {type(value)}"
    except TypeError as e:
        assert "json object must be a str or dict" in str(e)


# Test YAML edge cases
yaml_edge_cases = st.one_of(
    st.just("---\n"),  # Empty YAML document
    st.just("null"),   # YAML null
    st.just("~"),       # Another YAML null
    st.just("!!null"),  # Explicit null tag
    st.just("yes"),     # YAML boolean
    st.just("no"),      # YAML boolean
    st.just("on"),      # YAML boolean
    st.just("off"),     # YAML boolean
    st.just("true"),    # YAML boolean
    st.just("false"),   # YAML boolean
)

@given(yaml_edge_cases)
def test_validate_document_content_yaml_edge_cases(yaml_str):
    """Test that YAML edge cases are handled correctly"""
    result = ssm_validators.validate_document_content(yaml_str)
    assert result == yaml_str
    
    # Verify it's actually valid YAML
    parsed = yaml.safe_load(yaml_str)
    # Should parse without error


# Test S3 bucket name edge cases

@given(st.text(alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ", min_size=3, max_size=63))
def test_s3_bucket_uppercase_rejected(name):
    """Test that uppercase letters in S3 bucket names are rejected"""
    try:
        ssm_validators.s3_bucket_name(name)
        assert False, f"Should have rejected uppercase name: {name}"
    except ValueError as e:
        assert "is not a valid s3 bucket name" in str(e)


@given(st.text(alphabet=".-", min_size=3, max_size=63))
def test_s3_bucket_special_only_rejected(name):
    """Test that names with only dots and hyphens are rejected"""
    try:
        ssm_validators.s3_bucket_name(name)
        assert False, f"Should have rejected special-only name: {name}"
    except ValueError as e:
        assert "is not a valid s3 bucket name" in str(e)


@given(st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789.-", min_size=1, max_size=2))
def test_s3_bucket_too_short(name):
    """Test that S3 bucket names shorter than 3 characters are rejected"""
    try:
        ssm_validators.s3_bucket_name(name)
        assert False, f"Should have rejected short name: {name}"
    except ValueError as e:
        assert "is not a valid s3 bucket name" in str(e)


@given(st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789", min_size=64, max_size=100))
def test_s3_bucket_too_long(name):
    """Test that S3 bucket names longer than 63 characters are rejected"""
    try:
        ssm_validators.s3_bucket_name(name)
        assert False, f"Should have rejected long name: {name}"
    except ValueError as e:
        assert "is not a valid s3 bucket name" in str(e)


@given(st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789", min_size=2, max_size=61))
def test_s3_bucket_starting_with_dot(middle):
    """Test that S3 bucket names starting with dot are rejected"""
    name = "." + middle
    try:
        ssm_validators.s3_bucket_name(name)
        assert False, f"Should have rejected name starting with dot: {name}"
    except ValueError as e:
        assert "is not a valid s3 bucket name" in str(e)


@given(st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789", min_size=2, max_size=61))
def test_s3_bucket_ending_with_dot(middle):
    """Test that S3 bucket names ending with dot are rejected"""
    name = middle + "."
    try:
        ssm_validators.s3_bucket_name(name)
        assert False, f"Should have rejected name ending with dot: {name}"
    except ValueError as e:
        assert "is not a valid s3 bucket name" in str(e)


@given(st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789", min_size=2, max_size=61))
def test_s3_bucket_starting_with_hyphen(middle):
    """Test that S3 bucket names starting with hyphen are rejected"""
    name = "-" + middle
    try:
        ssm_validators.s3_bucket_name(name)
        assert False, f"Should have rejected name starting with hyphen: {name}"
    except ValueError as e:
        assert "is not a valid s3 bucket name" in str(e)


@given(st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789", min_size=2, max_size=61))
def test_s3_bucket_ending_with_hyphen(middle):
    """Test that S3 bucket names ending with hyphen are rejected"""
    name = middle + "-"
    try:
        ssm_validators.s3_bucket_name(name)
        assert False, f"Should have rejected name ending with hyphen: {name}"
    except ValueError as e:
        assert "is not a valid s3 bucket name" in str(e)


# Test Document with unusual but valid content

@given(st.dictionaries(
    st.text(alphabet="", min_size=0, max_size=0),  # Empty string keys
    st.integers()
))
def test_document_empty_string_keys(data):
    """Test Document with empty string keys in dict"""
    if "" in data:
        # Empty string is a valid key in Python dict and JSON
        doc = ssm.Document("TestDoc")
        doc.Content = data
        assert doc.Content == data
        
        # Also test as JSON string
        json_str = json.dumps(data)
        doc.Content = json_str
        assert doc.Content == json_str


# Test very large nested structures
large_nested = st.recursive(
    st.one_of(st.none(), st.booleans(), st.integers()),
    lambda children: st.dictionaries(
        st.text(min_size=1, max_size=5),
        children,
        min_size=0,
        max_size=3
    ),
    max_leaves=1000
)

@given(large_nested)
@settings(max_examples=50)
def test_validate_document_large_nested(data):
    """Test validation with deeply nested structures"""
    # As dict
    result = ssm_validators.validate_document_content(data)
    assert result == data
    
    # As JSON
    json_str = json.dumps(data)
    result = ssm_validators.validate_document_content(json_str)
    assert result == json_str
    
    # As YAML
    yaml_str = yaml.safe_dump(data)
    result = ssm_validators.validate_document_content(yaml_str)
    assert result == yaml_str