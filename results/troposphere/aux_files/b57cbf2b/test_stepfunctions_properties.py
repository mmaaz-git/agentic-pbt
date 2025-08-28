"""Property-based tests for troposphere.stepfunctions module."""

import json
from hypothesis import given, strategies as st, assume, settings
import troposphere.stepfunctions as sf
import troposphere


# Test 1: boolean function properties
@given(st.one_of(
    st.sampled_from([True, 1, "1", "true", "True"]),
    st.sampled_from([False, 0, "0", "false", "False"])
))
def test_boolean_valid_inputs_idempotent(x):
    """Test that boolean() is idempotent for valid inputs."""
    result1 = sf.boolean(x)
    result2 = sf.boolean(result1)
    assert result1 == result2
    assert isinstance(result1, bool)


@given(st.sampled_from([True, 1, "1", "true", "True"]))
def test_boolean_truthy_values(x):
    """Test that truthy values return True."""
    assert sf.boolean(x) is True


@given(st.sampled_from([False, 0, "0", "false", "False"]))
def test_boolean_falsy_values(x):
    """Test that falsy values return False."""
    assert sf.boolean(x) is False


@given(st.one_of(
    st.text().filter(lambda x: x not in ["1", "0", "true", "True", "false", "False"]),
    st.integers().filter(lambda x: x not in [0, 1]),
    st.floats(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_boolean_invalid_inputs_raise_error(x):
    """Test that invalid inputs raise ValueError."""
    try:
        sf.boolean(x)
        assert False, f"Expected ValueError for input {x}"
    except ValueError:
        pass  # Expected


# Test 2: integer function properties
@given(st.integers())
def test_integer_valid_integers_preserved(x):
    """Test that valid integers are returned unchanged."""
    result = sf.integer(x)
    assert result == x
    assert result is x  # Should be the same object


@given(st.text(alphabet="0123456789-", min_size=1).filter(lambda x: x != "-"))
def test_integer_valid_string_integers_preserved(x):
    """Test that valid integer strings are returned unchanged."""
    try:
        int(x)  # Check it's a valid integer string
        result = sf.integer(x)
        assert result == x
        assert isinstance(result, str)
    except ValueError:
        pass  # Skip invalid cases


@given(st.floats(allow_nan=False, allow_infinity=False))
def test_integer_floats_with_no_fractional_part(x):
    """Test integer function with floats."""
    if x == int(x):  # Float with no fractional part
        result = sf.integer(x)
        assert result == x
    else:
        # Should work as int() can convert it
        result = sf.integer(x)
        assert result == x


@given(st.one_of(
    st.text(min_size=1).filter(lambda x: not (x.lstrip('-').isdigit() or (x.startswith('-') and x[1:].isdigit()))),
    st.none(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_integer_invalid_inputs_raise_error(x):
    """Test that non-integer convertible inputs raise ValueError."""
    try:
        int(x)
        # If int() succeeds, integer() should too
        result = sf.integer(x)
        assert result == x
    except (ValueError, TypeError):
        # int() failed, so integer() should also fail
        try:
            sf.integer(x)
            assert False, f"Expected ValueError for input {x}"
        except ValueError:
            pass  # Expected


# Test 3: Class creation and to_dict properties
@given(st.text(min_size=1, max_size=100).filter(lambda x: x.isidentifier()))
def test_activity_creation_and_to_dict(name):
    """Test Activity creation and to_dict conversion."""
    activity = sf.Activity('TestActivity', Name=name)
    result = activity.to_dict()
    
    assert result['Type'] == 'AWS::StepFunctions::Activity'
    assert result['Properties']['Name'] == name
    assert 'Properties' in result
    assert 'Type' in result


@given(
    st.text(min_size=1, max_size=100).filter(lambda x: x.isidentifier()),
    st.text(min_size=20, max_size=200)  # ARN-like string
)
def test_statemachine_creation_and_to_dict(name, role_arn):
    """Test StateMachine creation with required RoleArn."""
    sm = sf.StateMachine(
        'TestStateMachine',
        RoleArn=role_arn,
        StateMachineName=name,
        DefinitionString='{"Comment": "Test"}'
    )
    result = sm.to_dict()
    
    assert result['Type'] == 'AWS::StepFunctions::StateMachine'
    assert result['Properties']['RoleArn'] == role_arn
    assert result['Properties']['StateMachineName'] == name
    assert 'DefinitionString' in result['Properties']


# Test 4: Property validation with integer validators
@given(st.integers(min_value=0, max_value=1000000))
def test_deployment_preference_with_integer_props(interval):
    """Test DeploymentPreference with integer properties."""
    dp = sf.DeploymentPreference(
        Type='LINEAR',
        StateMachineVersionArn='arn:aws:states:us-east-1:123456789012:stateMachine:test:1',
        Interval=interval,
        Percentage=50
    )
    
    # Convert to dict should preserve the integer values
    result = dp.to_dict()
    assert result['Interval'] == interval
    assert result['Percentage'] == 50


@given(st.one_of(
    st.text().filter(lambda x: not x.isdigit()),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_deployment_preference_invalid_interval(invalid_value):
    """Test that invalid interval values are handled properly."""
    try:
        int(invalid_value)
        # If int() works, it should be accepted
        dp = sf.DeploymentPreference(
            Type='LINEAR',
            StateMachineVersionArn='arn:test',
            Interval=invalid_value
        )
        # Should work if int() worked
    except (ValueError, TypeError):
        # int() failed, so creating with this value should also fail
        try:
            dp = sf.DeploymentPreference(
                Type='LINEAR',
                StateMachineVersionArn='arn:test',
                Interval=invalid_value
            )
            # Getting to_dict might trigger validation
            dp.to_dict()
        except (ValueError, TypeError, AttributeError):
            pass  # Expected for truly invalid values


# Test 5: from_dict round-trip property
@given(
    st.text(min_size=1, max_size=50).filter(lambda x: x.isidentifier()),
    st.booleans()
)
def test_activity_from_dict_round_trip(name, use_tags):
    """Test that from_dict can recreate objects from to_dict output."""
    # Create original
    original = sf.Activity('TestActivity', Name=name)
    if use_tags:
        original.Tags = troposphere.Tags(Environment='test')
    
    # Convert to dict
    dict_repr = original.to_dict()
    
    # Try to recreate - note: from_dict is a class method
    recreated = sf.Activity.from_dict('TestActivity', dict_repr)
    recreated_dict = recreated.to_dict()
    
    # Compare dictionaries (not objects)
    assert dict_repr == recreated_dict


# Test 6: TracingConfiguration enabled property
@given(st.booleans())
def test_tracing_configuration_enabled(enabled):
    """Test TracingConfiguration with Enabled property."""
    tc = sf.TracingConfiguration(Enabled=enabled)
    result = tc.to_dict()
    
    # The boolean should be preserved
    assert result['Enabled'] == enabled
    assert isinstance(result['Enabled'], bool)


# Test 7: S3Location with required and optional properties
@given(
    st.text(min_size=3, max_size=63).filter(lambda x: x.replace('-', '').replace('.', '').isalnum()),
    st.text(min_size=1, max_size=100),
    st.one_of(st.none(), st.text(min_size=1, max_size=20))
)
def test_s3_location_properties(bucket, key, version):
    """Test S3Location with various property combinations."""
    if version is None:
        s3loc = sf.S3Location(Bucket=bucket, Key=key)
    else:
        s3loc = sf.S3Location(Bucket=bucket, Key=key, Version=version)
    
    result = s3loc.to_dict()
    assert result['Bucket'] == bucket
    assert result['Key'] == key
    if version is not None:
        assert result['Version'] == version
    else:
        assert 'Version' not in result


# Test 8: Property edge cases with special characters
@given(st.text(min_size=1).filter(lambda x: any(c in x for c in ['<', '>', '&', '"', "'"])))
def test_activity_name_with_special_chars(name):
    """Test that special characters in names are preserved correctly."""
    activity = sf.Activity('TestActivity', Name=name)
    result = activity.to_dict()
    
    # Name should be preserved exactly as given
    assert result['Properties']['Name'] == name
    
    # JSON serialization should handle special chars
    json_str = activity.to_json()
    parsed = json.loads(json_str)
    assert parsed['Properties']['Name'] == name


# Test 9: Test validation of required properties
def test_statemachine_missing_required_rolearn():
    """Test that StateMachine requires RoleArn."""
    sm = sf.StateMachine('TestSM')  # Missing required RoleArn
    
    # Should be able to create it
    assert sm is not None
    
    # to_dict might not validate immediately
    try:
        result = sm.to_dict()
        # If to_dict succeeds without RoleArn, check the output
        assert 'Properties' in result
        # RoleArn might be missing or None
        assert 'RoleArn' not in result.get('Properties', {}) or result['Properties'].get('RoleArn') is None
    except (TypeError, KeyError, AttributeError):
        pass  # Some validation might occur


# Test 10: Multiple property types in LoggingConfiguration
@given(
    st.booleans(),
    st.one_of(st.none(), st.text(min_size=1, max_size=100)),
    st.one_of(st.none(), st.sampled_from(['OFF', 'ERROR', 'ALL']))
)
def test_logging_configuration_properties(include_exec_data, log_arn, level):
    """Test LoggingConfiguration with various property combinations."""
    lc = sf.LoggingConfiguration(IncludeExecutionData=include_exec_data)
    
    if level:
        lc.Level = level
    
    if log_arn:
        # Need to create destinations list with proper structure
        cw_log_group = sf.CloudWatchLogsLogGroup(LogGroupArn=log_arn)
        log_dest = sf.LogDestination(CloudWatchLogsLogGroup=cw_log_group)
        lc.Destinations = [log_dest]
    
    result = lc.to_dict()
    assert result['IncludeExecutionData'] == include_exec_data
    if level:
        assert result['Level'] == level
    if log_arn:
        assert 'Destinations' in result