#!/usr/bin/env python3
"""Property-based tests for troposphere.awslambda module."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import re
import string
from hypothesis import given, strategies as st, assume, settings
import troposphere.awslambda as awslambda
from troposphere import Join


# Test 1: Memory size validation
@given(st.integers())
def test_memory_size_validation_bounds(memory):
    """Test that validate_memory_size correctly enforces bounds."""
    from troposphere.validators.awslambda import validate_memory_size, MINIMUM_MEMORY, MAXIMUM_MEMORY
    
    if memory < MINIMUM_MEMORY or memory > MAXIMUM_MEMORY:
        # Should raise ValueError for out-of-bounds values
        try:
            validate_memory_size(memory)
            assert False, f"Expected ValueError for memory {memory}"
        except ValueError as e:
            assert "Lambda Function memory size must be between" in str(e)
    else:
        # Should accept values within bounds
        result = validate_memory_size(memory)
        assert result == memory


@given(st.floats(allow_nan=False, allow_infinity=False))
def test_memory_size_with_floats(memory):
    """Test that validate_memory_size handles float inputs."""
    from troposphere.validators.awslambda import validate_memory_size, MINIMUM_MEMORY, MAXIMUM_MEMORY
    
    try:
        memory_int = int(memory)
    except (ValueError, OverflowError):
        # Should fail for non-convertible floats
        try:
            validate_memory_size(memory)
            assert False, f"Expected error for non-convertible float {memory}"
        except:
            pass
        return
    
    if memory_int < MINIMUM_MEMORY or memory_int > MAXIMUM_MEMORY:
        try:
            validate_memory_size(memory)
            assert False, f"Expected ValueError for memory {memory}"
        except ValueError as e:
            assert "Lambda Function memory size must be between" in str(e)
    else:
        result = validate_memory_size(memory)
        assert result == memory_int


# Test 2: Package type validation
@given(st.text())
def test_package_type_validation(package_type):
    """Test that validate_package_type only accepts 'Image' or 'Zip'."""
    from troposphere.validators.awslambda import validate_package_type
    
    if package_type in ["Image", "Zip"]:
        result = validate_package_type(package_type)
        assert result == package_type
    else:
        try:
            validate_package_type(package_type)
            assert False, f"Expected ValueError for package type '{package_type}'"
        except ValueError as e:
            assert "Lambda Function PackageType must be one of" in str(e)


# Test 3: Environment variable name validation
@given(st.dictionaries(st.text(), st.text()))
def test_environment_variables_validation(variables):
    """Test environment variable name validation rules."""
    from troposphere.validators.awslambda import validate_variables_name
    
    RESERVED_ENVIRONMENT_VARIABLES = [
        "AWS_ACCESS_KEY", "AWS_ACCESS_KEY_ID", "AWS_DEFAULT_REGION",
        "AWS_EXECUTION_ENV", "AWS_LAMBDA_FUNCTION_MEMORY_SIZE",
        "AWS_LAMBDA_FUNCTION_NAME", "AWS_LAMBDA_FUNCTION_VERSION",
        "AWS_LAMBDA_LOG_GROUP_NAME", "AWS_LAMBDA_LOG_STREAM_NAME",
        "AWS_REGION", "AWS_SECRET_ACCESS_KEY", "AWS_SECRET_KEY",
        "AWS_SECURITY_TOKEN", "AWS_SESSION_TOKEN",
        "LAMBDA_RUNTIME_DIR", "LAMBDA_TASK_ROOT"
    ]
    ENVIRONMENT_VARIABLES_NAME_PATTERN = r"^[a-zA-Z][a-zA-Z0-9_]+$"
    
    should_fail = False
    for name in variables.keys():
        if name in RESERVED_ENVIRONMENT_VARIABLES:
            should_fail = True
            break
        if not re.match(ENVIRONMENT_VARIABLES_NAME_PATTERN, name):
            should_fail = True
            break
    
    if should_fail:
        try:
            validate_variables_name(variables)
            assert False, f"Expected ValueError for variables {variables}"
        except ValueError:
            pass
    else:
        result = validate_variables_name(variables)
        assert result == variables


@given(st.lists(st.text()))
def test_environment_variables_reserved_names(names):
    """Test that reserved environment variable names are rejected."""
    from troposphere.validators.awslambda import validate_variables_name
    
    RESERVED = [
        "AWS_ACCESS_KEY", "AWS_ACCESS_KEY_ID", "AWS_DEFAULT_REGION",
        "AWS_EXECUTION_ENV", "AWS_LAMBDA_FUNCTION_MEMORY_SIZE",
        "AWS_LAMBDA_FUNCTION_NAME", "AWS_LAMBDA_FUNCTION_VERSION",
        "AWS_LAMBDA_LOG_GROUP_NAME", "AWS_LAMBDA_LOG_STREAM_NAME",
        "AWS_REGION", "AWS_SECRET_ACCESS_KEY", "AWS_SECRET_KEY",
        "AWS_SECURITY_TOKEN", "AWS_SESSION_TOKEN",
        "LAMBDA_RUNTIME_DIR", "LAMBDA_TASK_ROOT"
    ]
    
    # Convert list to dict for the function
    variables = {name: "value" for name in names}
    
    has_reserved = any(name in RESERVED for name in names)
    
    if has_reserved:
        try:
            validate_variables_name(variables)
            assert False, f"Expected ValueError for reserved names in {names}"
        except ValueError as e:
            assert "can't be none of" in str(e)
    else:
        # Still need to check pattern
        pattern = r"^[a-zA-Z][a-zA-Z0-9_]+$"
        has_invalid_pattern = any(not re.match(pattern, name) for name in names)
        
        if has_invalid_pattern:
            try:
                validate_variables_name(variables)
                assert False, f"Expected ValueError for invalid pattern in {names}"
            except ValueError as e:
                assert "Invalid environment variable name" in str(e)
        else:
            result = validate_variables_name(variables)
            assert result == variables


# Test 4: Code validation - mutual exclusivity
@given(
    st.booleans(),  # has_image_uri
    st.booleans(),  # has_zip_file  
    st.booleans(),  # has_s3_bucket
    st.booleans(),  # has_s3_key
    st.booleans(),  # has_s3_object_version
)
def test_code_validation_mutual_exclusivity(has_image_uri, has_zip_file, has_s3_bucket, has_s3_key, has_s3_object_version):
    """Test that Code validation enforces mutual exclusivity rules."""
    
    code = awslambda.Code()
    
    if has_image_uri:
        code.properties["ImageUri"] = "test-image-uri"
    if has_zip_file:
        code.properties["ZipFile"] = "test content"
    if has_s3_bucket:
        code.properties["S3Bucket"] = "test-bucket"
    if has_s3_key:
        code.properties["S3Key"] = "test-key"
    if has_s3_object_version:
        code.properties["S3ObjectVersion"] = "test-version"
    
    # Determine if this should fail
    should_fail = False
    error_msg = None
    
    # Check mutual exclusivity rules
    if has_zip_file and has_image_uri:
        should_fail = True
        error_msg = "You can't specify both 'ImageUri' and 'ZipFile'"
    elif has_zip_file and has_s3_bucket:
        should_fail = True
        error_msg = "You can't specify both 'S3Bucket' and 'ZipFile'"
    elif has_zip_file and has_s3_key:
        should_fail = True
        error_msg = "You can't specify both 'S3Key' and 'ZipFile'"
    elif has_zip_file and has_s3_object_version:
        should_fail = True  
        error_msg = "You can't specify both 'S3ObjectVersion' and 'ZipFile'"
    elif has_image_uri and (has_s3_bucket or has_s3_key or has_s3_object_version):
        should_fail = True
        error_msg = "You can't specify 'ImageUri' and any of 'S3Bucket'"
    elif not has_zip_file and not (has_s3_bucket and has_s3_key) and not has_image_uri:
        should_fail = True
        error_msg = "You must specify a bucket location"
    
    if should_fail:
        try:
            code.validate()
            assert False, f"Expected ValueError for combination: ImageUri={has_image_uri}, ZipFile={has_zip_file}, S3Bucket={has_s3_bucket}, S3Key={has_s3_key}"
        except ValueError as e:
            if error_msg:
                assert error_msg in str(e) or "You must specify" in str(e)
    else:
        # Should succeed
        code.validate()


# Test 5: ImageConfig validation - length limits
@given(
    st.lists(st.text(), min_size=0, max_size=2000),
    st.lists(st.text(), min_size=0, max_size=2000),
    st.text(max_size=1500)
)
def test_image_config_validation(command, entry_point, working_dir):
    """Test ImageConfig length limits."""
    
    config = awslambda.ImageConfig()
    
    if command:
        config.properties["Command"] = command
    if entry_point:
        config.properties["EntryPoint"] = entry_point
    if working_dir:
        config.properties["WorkingDirectory"] = working_dir
    
    should_fail = False
    
    if command and len(command) > 1500:
        should_fail = True
    elif entry_point and len(entry_point) > 1500:
        should_fail = True
    elif working_dir and len(working_dir) > 1000:
        should_fail = True
    
    if should_fail:
        try:
            config.validate()
            assert False, f"Expected ValueError for lengths: Command={len(command) if command else 0}, EntryPoint={len(entry_point) if entry_point else 0}, WorkingDir={len(working_dir)}"
        except ValueError as e:
            assert "Maximum" in str(e)
    else:
        config.validate()


# Test 6: ZipFile length validation
@given(st.text())
def test_zipfile_length_validation(content):
    """Test that ZipFile content is limited to 4MB."""
    from troposphere.validators.awslambda import check_zip_file
    
    MAX_LENGTH = 4 * 1024 * 1024  # 4MB
    
    if len(content) > MAX_LENGTH:
        try:
            check_zip_file(content)
            assert False, f"Expected ValueError for ZipFile length {len(content)}"
        except ValueError as e:
            assert "ZipFile length cannot exceed" in str(e)
    else:
        # Should not raise
        check_zip_file(content)


@given(st.integers(min_value=0, max_value=5*1024*1024))
def test_zipfile_with_specific_sizes(size):
    """Test ZipFile validation with specific sizes."""
    from troposphere.validators.awslambda import check_zip_file
    
    MAX_LENGTH = 4 * 1024 * 1024  # 4MB
    content = "x" * size
    
    if size > MAX_LENGTH:
        try:
            check_zip_file(content)
            assert False, f"Expected ValueError for ZipFile size {size}"
        except ValueError as e:
            assert "ZipFile length cannot exceed" in str(e)
            assert str(MAX_LENGTH) in str(e)
    else:
        check_zip_file(content)


# Test 7: Test Join handling in ZipFile validation
@given(
    st.text(max_size=1000),  # delimiter
    st.lists(st.text(max_size=1000), min_size=0, max_size=10)  # values
)
def test_zipfile_join_validation(delimiter, values):
    """Test that ZipFile validation handles Join objects correctly."""
    from troposphere.validators.awslambda import check_zip_file
    
    MAX_LENGTH = 4 * 1024 * 1024  # 4MB
    
    # Create a Join object
    join_obj = Join(delimiter, values)
    
    # Calculate expected length
    if not values or len(values) == 0:
        # Should pass - no values to join
        check_zip_file(join_obj)
        return
    
    total_length = sum(len(v) for v in values if isinstance(v, str))
    total_length += (len(values) - 1) * len(delimiter)
    
    if total_length > MAX_LENGTH:
        try:
            check_zip_file(join_obj)
            assert False, f"Expected ValueError for Join with total length {total_length}"
        except ValueError as e:
            assert "ZipFile length cannot exceed" in str(e)
    else:
        check_zip_file(join_obj)


# Additional test for edge cases in memory validation
@given(st.text())
def test_memory_size_with_non_numeric_strings(memory_str):
    """Test memory size validation with non-numeric string inputs."""
    from troposphere.validators.awslambda import validate_memory_size
    
    try:
        # Try to convert to int first (as the function does)
        memory_int = int(memory_str)
        # If conversion succeeds, apply normal validation
        if memory_int < 128 or memory_int > 10240:
            try:
                validate_memory_size(memory_str)
                assert False
            except ValueError as e:
                assert "Lambda Function memory size must be between" in str(e)
        else:
            result = validate_memory_size(memory_str)
            assert result == memory_int
    except (ValueError, TypeError):
        # String is not numeric - should fail
        try:
            validate_memory_size(memory_str)
            assert False, f"Expected error for non-numeric string '{memory_str}'"
        except (ValueError, TypeError):
            pass


if __name__ == "__main__":
    # Run all tests
    import pytest
    pytest.main([__file__, "-v"])