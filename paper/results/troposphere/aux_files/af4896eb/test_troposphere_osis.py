import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import json
from hypothesis import given, strategies as st, assume, settings
import troposphere.osis as osis
import troposphere.validators as validators


# Test boolean validator
@given(st.one_of(
    st.just(True), st.just(1), st.just("1"), st.just("true"), st.just("True"),
    st.just(False), st.just(0), st.just("0"), st.just("false"), st.just("False")
))
def test_boolean_validator_valid_inputs(value):
    """Test that boolean validator accepts documented valid inputs."""
    result = validators.boolean(value)
    assert isinstance(result, bool)
    if value in [True, 1, "1", "true", "True"]:
        assert result is True
    else:
        assert result is False


@given(st.one_of(
    st.integers().filter(lambda x: x not in [0, 1]),
    st.text().filter(lambda x: x not in ["0", "1", "true", "True", "false", "False"]),
    st.floats(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_boolean_validator_invalid_inputs(value):
    """Test that boolean validator raises ValueError for invalid inputs."""
    try:
        validators.boolean(value)
        assert False, f"Should have raised ValueError for {value}"
    except ValueError:
        pass  # Expected


# Test integer validator
@given(st.integers())
def test_integer_validator_accepts_integers(value):
    """Test that integer validator accepts all integers."""
    result = validators.integer(value)
    assert result == value
    assert int(result) == value


@given(st.text(min_size=1).map(str))
def test_integer_validator_accepts_numeric_strings(value):
    """Test that integer validator accepts numeric strings."""
    try:
        int(value)
        is_valid_int_string = True
    except ValueError:
        is_valid_int_string = False
    
    if is_valid_int_string:
        result = validators.integer(value)
        assert result == value
    else:
        try:
            validators.integer(value)
            assert False, f"Should have raised ValueError for {value}"
        except ValueError:
            pass


@given(st.one_of(
    st.floats().filter(lambda x: not x.is_integer()),
    st.text().filter(lambda x: not x.lstrip('-').isdigit()),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_integer_validator_rejects_non_integers(value):
    """Test that integer validator rejects non-integer values."""
    # Skip integer-like floats
    if isinstance(value, float) and value.is_integer():
        assume(False)
    # Skip numeric strings
    if isinstance(value, str):
        try:
            int(value)
            assume(False)
        except (ValueError, TypeError):
            pass
    
    try:
        validators.integer(value)
        assert False, f"Should have raised ValueError for {value}"
    except ValueError:
        pass


# Test AWS classes with boolean properties
@given(st.booleans())
def test_buffer_options_boolean_property(value):
    """Test that BufferOptions correctly handles boolean properties."""
    buffer_opts = osis.BufferOptions(PersistentBufferEnabled=value)
    assert buffer_opts.PersistentBufferEnabled == value
    
    # Test to_dict
    result = buffer_opts.to_dict()
    assert result['PersistentBufferEnabled'] == value


@given(st.one_of(st.just(0), st.just(1), st.just("true"), st.just("false")))
def test_buffer_options_boolean_coercion(value):
    """Test that BufferOptions correctly coerces boolean-like values."""
    buffer_opts = osis.BufferOptions(PersistentBufferEnabled=value)
    expected = value in [1, "true", "True"]
    if value == 0 or value == "false":
        expected = False
    assert buffer_opts.PersistentBufferEnabled == expected


# Test AWS classes with integer properties
@given(st.integers(min_value=0, max_value=1000))
def test_pipeline_integer_properties(value):
    """Test that Pipeline correctly handles integer properties."""
    pipeline = osis.Pipeline(
        "TestPipeline",
        MinUnits=value,
        MaxUnits=value + 1,
        PipelineName="test-pipeline",
        PipelineConfigurationBody="test config"
    )
    assert pipeline.MinUnits == value
    assert pipeline.MaxUnits == value + 1
    
    # Test to_dict
    result = pipeline.to_dict()
    assert result['Properties']['MinUnits'] == value
    assert result['Properties']['MaxUnits'] == value + 1


# Test list properties
@given(st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=5))
def test_vpc_options_list_properties(subnet_ids):
    """Test that VpcOptions correctly handles list properties."""
    vpc_opts = osis.VpcOptions(SubnetIds=subnet_ids)
    assert vpc_opts.SubnetIds == subnet_ids
    
    # Test to_dict
    result = vpc_opts.to_dict()
    assert result['SubnetIds'] == subnet_ids


# Test nested properties
@given(st.text(min_size=1, max_size=50))
def test_nested_properties(log_group):
    """Test that nested AWS properties work correctly."""
    cloudwatch_dest = osis.CloudWatchLogDestination(LogGroup=log_group)
    log_opts = osis.LogPublishingOptions(CloudWatchLogDestination=cloudwatch_dest)
    
    assert log_opts.CloudWatchLogDestination.LogGroup == log_group
    
    # Test to_dict
    result = log_opts.to_dict()
    assert result['CloudWatchLogDestination']['LogGroup'] == log_group


# Test round-trip property for simple classes
@given(st.booleans())
def test_buffer_options_roundtrip(enabled):
    """Test that BufferOptions can be serialized and deserialized."""
    original = osis.BufferOptions(PersistentBufferEnabled=enabled)
    dict_repr = original.to_dict()
    
    # Recreate from dict
    recreated = osis.BufferOptions._from_dict(**dict_repr)
    
    # Verify they're equivalent
    assert recreated.PersistentBufferEnabled == original.PersistentBufferEnabled
    assert recreated.to_dict() == original.to_dict()


@given(
    st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=3),
    st.lists(st.text(min_size=1, max_size=20), min_size=0, max_size=3)
)
def test_vpc_options_roundtrip(subnet_ids, security_group_ids):
    """Test VpcOptions round-trip serialization."""
    original = osis.VpcOptions(
        SubnetIds=subnet_ids,
        SecurityGroupIds=security_group_ids if security_group_ids else None
    )
    dict_repr = original.to_dict()
    
    # Recreate from dict
    recreated = osis.VpcOptions._from_dict(**dict_repr)
    
    # Verify they're equivalent
    assert recreated.SubnetIds == original.SubnetIds
    if security_group_ids:
        assert recreated.SecurityGroupIds == original.SecurityGroupIds
    assert recreated.to_dict() == original.to_dict()


# Test complex nested round-trip
@given(
    st.booleans(),
    st.booleans(),
    st.text(min_size=1, max_size=30)
)
def test_log_publishing_options_roundtrip(is_enabled, attach_to_vpc, cidr_block):
    """Test LogPublishingOptions with nested properties round-trip."""
    cloudwatch = osis.CloudWatchLogDestination(LogGroup="test-log-group")
    original = osis.LogPublishingOptions(
        CloudWatchLogDestination=cloudwatch,
        IsLoggingEnabled=is_enabled
    )
    
    dict_repr = original.to_dict()
    
    # Recreate from dict
    recreated = osis.LogPublishingOptions._from_dict(**dict_repr)
    
    # Verify they're equivalent
    assert recreated.IsLoggingEnabled == original.IsLoggingEnabled
    assert recreated.CloudWatchLogDestination.LogGroup == "test-log-group"
    assert recreated.to_dict() == original.to_dict()


# Test that invalid types are rejected
@given(st.one_of(
    st.integers(),
    st.floats(),
    st.lists(st.text()),
    st.dictionaries(st.text(), st.integers())
))
def test_string_property_type_validation(invalid_value):
    """Test that string properties reject non-string values."""
    # Skip strings
    if isinstance(invalid_value, str):
        assume(False)
    
    try:
        osis.CloudWatchLogDestination(LogGroup=invalid_value)
        # Some values might be coerced to strings, check if that happened
        assert False, f"Should have raised TypeError for {invalid_value}"
    except (TypeError, AttributeError):
        pass  # Expected


# Test Pipeline validation with all properties
@given(
    st.integers(min_value=1, max_value=100),
    st.integers(min_value=1, max_value=100),
    st.text(min_size=1, max_size=50).filter(lambda x: x.replace('-', '').replace('_', '').isalnum()),
    st.text(min_size=1, max_size=200),
    st.booleans()
)
@settings(max_examples=50)
def test_pipeline_full_creation(min_units, max_units, pipeline_name, config_body, buffer_enabled):
    """Test creating a full Pipeline with various properties."""
    # Ensure max >= min
    if max_units < min_units:
        max_units = min_units
    
    buffer_opts = osis.BufferOptions(PersistentBufferEnabled=buffer_enabled)
    
    pipeline = osis.Pipeline(
        "TestPipeline",
        MinUnits=min_units,
        MaxUnits=max_units,
        PipelineName=pipeline_name,
        PipelineConfigurationBody=config_body,
        BufferOptions=buffer_opts
    )
    
    # Verify properties
    assert pipeline.MinUnits == min_units
    assert pipeline.MaxUnits == max_units
    assert pipeline.PipelineName == pipeline_name
    assert pipeline.PipelineConfigurationBody == config_body
    assert pipeline.BufferOptions.PersistentBufferEnabled == buffer_enabled
    
    # Test serialization
    result = pipeline.to_dict()
    assert result['Type'] == 'AWS::OSIS::Pipeline'
    assert result['Properties']['MinUnits'] == min_units
    assert result['Properties']['MaxUnits'] == max_units
    assert result['Properties']['PipelineName'] == pipeline_name
    assert result['Properties']['BufferOptions']['PersistentBufferEnabled'] == buffer_enabled


# Test that title validation works
@given(st.text())
def test_pipeline_title_validation(title):
    """Test that Pipeline title validation follows alphanumeric rules."""
    try:
        pipeline = osis.Pipeline(
            title,
            MinUnits=1,
            MaxUnits=2,
            PipelineName="test",
            PipelineConfigurationBody="test"
        )
        # If it succeeded, title should be alphanumeric
        assert title.replace('_', '').isalnum() or title == ""
    except ValueError as e:
        # If it failed, title should not be alphanumeric
        if "not alphanumeric" in str(e):
            assert not title.isalnum() or not title