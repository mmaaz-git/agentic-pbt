import json
from hypothesis import given, strategies as st, assume, settings
import troposphere.synthetics as synthetics
from troposphere.validators import boolean, integer
from troposphere.validators.synthetics import canary_runtime_version


# Test 1: boolean validator round-trip property
@given(st.sampled_from([True, 1, "1", "true", "True", False, 0, "0", "false", "False"]))
def test_boolean_validator_idempotence(value):
    """boolean validator should be idempotent - f(f(x)) = f(x)"""
    result1 = boolean(value)
    result2 = boolean(result1)
    assert result1 == result2
    assert isinstance(result1, bool)


# Test 2: integer validator preserves integer values
@given(st.integers())
def test_integer_validator_preserves_integers(value):
    """integer validator should preserve integer values"""
    result = integer(value)
    assert int(result) == value


# Test 3: integer validator handles string representations
@given(st.integers())
def test_integer_validator_string_round_trip(value):
    """integer validator should handle string representations correctly"""
    str_value = str(value)
    result = integer(str_value)
    assert int(result) == value


# Test 4: canary_runtime_version validator rejects invalid versions
@given(st.text())
def test_canary_runtime_version_validation(version):
    """canary_runtime_version should only accept valid runtime versions"""
    valid_versions = [
        "syn-nodejs-playwright-1.0",
        "syn-nodejs-puppeteer-4.0",
        "syn-nodejs-puppeteer-5.0",
        "syn-nodejs-puppeteer-5.1",
        "syn-nodejs-puppeteer-5.2",
        "syn-nodejs-puppeteer-6.0",
        "syn-nodejs-puppeteer-6.1",
        "syn-nodejs-puppeteer-6.2",
        "syn-nodejs-puppeteer-7.0",
        "syn-nodejs-puppeteer-8.0",
        "syn-nodejs-puppeteer-9.0",
        "syn-nodejs-puppeteer-9.1",
        "syn-python-selenium-1.0",
        "syn-python-selenium-1.1",
        "syn-python-selenium-1.2",
        "syn-python-selenium-1.3",
        "syn-python-selenium-2.0",
        "syn-python-selenium-2.1",
        "syn-python-selenium-3.0",
        "syn-python-selenium-4.0",
        "syn-python-selenium-4.1",
    ]
    
    if version in valid_versions:
        result = canary_runtime_version(version)
        assert result == version
    else:
        try:
            canary_runtime_version(version)
            assert False, f"Should have raised ValueError for invalid version: {version}"
        except ValueError as e:
            assert "RuntimeVersion must be one of" in str(e)


# Test 5: Property with integer validator maintains value
@given(st.integers(min_value=0, max_value=100000))
def test_runconfig_integer_properties(memory_value):
    """RunConfig integer properties should preserve values through validation"""
    config = synthetics.RunConfig(MemoryInMB=memory_value)
    assert config.properties["MemoryInMB"] == memory_value
    assert int(config.properties["MemoryInMB"]) == memory_value


# Test 6: Property with boolean validator converts correctly
@given(st.sampled_from([True, 1, "1", "true", "True", False, 0, "0", "false", "False"]))
def test_runconfig_boolean_properties(active_tracing_value):
    """RunConfig boolean properties should convert values to boolean"""
    config = synthetics.RunConfig(ActiveTracing=active_tracing_value)
    result = config.properties["ActiveTracing"]
    assert isinstance(result, bool)
    # Check conversion is correct
    if active_tracing_value in [True, 1, "1", "true", "True"]:
        assert result is True
    else:
        assert result is False


# Test 7: to_dict and from_dict round-trip for simple properties
@given(
    st.text(min_size=1, max_size=100),
    st.text(min_size=1, max_size=100)
)
def test_s3encryption_roundtrip(mode, arn):
    """S3Encryption should preserve data through to_dict/from_dict round-trip"""
    original = synthetics.S3Encryption(
        EncryptionMode=mode,
        KmsKeyArn=arn
    )
    
    dict_repr = original.to_dict()
    restored = synthetics.S3Encryption.from_dict("test", dict_repr)
    
    assert restored.properties.get("EncryptionMode") == mode
    assert restored.properties.get("KmsKeyArn") == arn


# Test 8: Required properties enforcement
@given(st.text(min_size=1, max_size=100))
def test_code_required_handler(handler):
    """Code object requires Handler property"""
    code = synthetics.Code(Handler=handler)
    assert code.properties["Handler"] == handler
    
    # Test that it's actually stored
    dict_repr = code.to_dict()
    assert dict_repr["Handler"] == handler


# Test 9: List properties maintain list type
@given(st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=10))
def test_vpcconfig_list_properties(security_groups):
    """VPCConfig list properties should maintain list type and elements"""
    subnet_ids = ["subnet-" + str(i) for i in range(3)]
    config = synthetics.VPCConfig(
        SecurityGroupIds=security_groups,
        SubnetIds=subnet_ids
    )
    
    assert isinstance(config.properties["SecurityGroupIds"], list)
    assert config.properties["SecurityGroupIds"] == security_groups
    assert isinstance(config.properties["SubnetIds"], list)
    assert config.properties["SubnetIds"] == subnet_ids


# Test 10: Complex nested property validation
@given(
    st.text(min_size=1, max_size=100),
    st.text(min_size=1, max_size=100)
)
def test_artifact_config_nested_s3encryption(mode, arn):
    """ArtifactConfig should correctly handle nested S3Encryption"""
    s3_encryption = synthetics.S3Encryption(
        EncryptionMode=mode,
        KmsKeyArn=arn
    )
    
    artifact_config = synthetics.ArtifactConfig(
        S3Encryption=s3_encryption
    )
    
    assert artifact_config.properties["S3Encryption"] == s3_encryption
    # Check the nested object maintains its properties
    assert s3_encryption.properties.get("EncryptionMode") == mode
    assert s3_encryption.properties.get("KmsKeyArn") == arn


# Test 11: RetryConfig MaxRetries validation with edge cases
@given(st.one_of(
    st.integers(),
    st.text(),
    st.floats(allow_nan=False, allow_infinity=False)
))
def test_retry_config_max_retries_type_handling(value):
    """RetryConfig should handle various types for MaxRetries through integer validator"""
    try:
        # Try to convert to int first to predict if it should work
        int_value = int(value)
        config = synthetics.RetryConfig(MaxRetries=value)
        assert int(config.properties["MaxRetries"]) == int_value
    except (ValueError, TypeError):
        # Should raise an error for non-integer convertible values
        try:
            synthetics.RetryConfig(MaxRetries=value)
            assert False, f"Should have raised error for non-integer value: {value}"
        except (ValueError, TypeError):
            pass  # Expected behavior


# Test 12: BaseScreenshot with list of ignore coordinates
@given(
    st.lists(st.text(min_size=1, max_size=50), min_size=0, max_size=10),
    st.text(min_size=1, max_size=100)
)
def test_base_screenshot_ignore_coordinates(coords, name):
    """BaseScreenshot should handle list of ignore coordinates"""
    screenshot = synthetics.BaseScreenshot(
        IgnoreCoordinates=coords,
        ScreenshotName=name
    )
    
    assert screenshot.properties["ScreenshotName"] == name
    if coords:
        assert screenshot.properties["IgnoreCoordinates"] == coords
        assert isinstance(screenshot.properties["IgnoreCoordinates"], list)


# Test 13: Group ResourceArns list property
@given(
    st.text(min_size=1, max_size=100, alphabet=st.sampled_from("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")),
    st.lists(st.text(min_size=1, max_size=200), min_size=0, max_size=20)
)
def test_group_resource_arns(title, arns):
    """Group should handle ResourceArns list property correctly"""
    group = synthetics.Group(title, Name="TestGroup", ResourceArns=arns)
    
    assert group.properties["Name"] == "TestGroup"
    if arns:
        assert group.properties["ResourceArns"] == arns
        assert isinstance(group.properties["ResourceArns"], list)


# Test 14: JSON serialization round-trip
@given(
    st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    st.text(min_size=1, max_size=100).filter(lambda x: x.strip())
)
def test_json_serialization_roundtrip(mode, arn):
    """Objects should survive JSON serialization round-trip"""
    original = synthetics.S3Encryption(
        EncryptionMode=mode,
        KmsKeyArn=arn
    )
    
    json_str = original.to_json()
    parsed = json.loads(json_str)
    
    assert parsed.get("EncryptionMode") == mode
    assert parsed.get("KmsKeyArn") == arn