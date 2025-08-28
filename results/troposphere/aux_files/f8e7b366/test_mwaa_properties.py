#!/usr/bin/env python3
"""Property-based tests for troposphere.mwaa module"""

import string
from hypothesis import given, strategies as st, assume, settings
import troposphere.mwaa as mwaa
from troposphere.validators import boolean, integer


# Test 1: Boolean validator property
@given(
    st.one_of(
        st.sampled_from([True, 1, "1", "true", "True", False, 0, "0", "false", "False"]),
        st.text(),
        st.integers(),
        st.floats(),
        st.none()
    )
)
def test_boolean_validator(value):
    """Test that boolean validator correctly handles various input types"""
    valid_true = [True, 1, "1", "true", "True"]
    valid_false = [False, 0, "0", "false", "False"]
    
    if value in valid_true:
        assert boolean(value) is True
    elif value in valid_false:
        assert boolean(value) is False
    else:
        try:
            result = boolean(value)
            # If it doesn't raise, it should return a boolean
            assert isinstance(result, bool)
        except ValueError:
            # Expected for invalid inputs
            pass


# Test 2: Integer validator property
@given(
    st.one_of(
        st.integers(),
        st.text(),
        st.floats(),
        st.none(),
        st.lists(st.integers())
    )
)
def test_integer_validator(value):
    """Test that integer validator accepts valid integers and rejects invalid ones"""
    try:
        result = integer(value)
        # If it succeeds, we should be able to convert result to int
        int_val = int(result)
        # And converting the original value should give the same result
        assert int(value) == int_val
    except (ValueError, TypeError):
        # Should fail for non-integer-convertible values
        # Verify that it indeed cannot be converted to int
        try:
            int(value)
            # If we can convert it, the validator should have accepted it
            assert False, f"integer() rejected {value} but int() accepts it"
        except (ValueError, TypeError):
            # Expected - both should fail
            pass


# Test 3: Title validation for MWAA Environment
@given(st.text())
def test_environment_title_validation(title):
    """Test that Environment title validation follows alphanumeric rules"""
    try:
        env = mwaa.Environment(title)
        # If it succeeds, title should be alphanumeric
        assert title is not None
        assert len(title) > 0
        assert all(c in string.ascii_letters + string.digits for c in title)
    except ValueError as e:
        # Should fail for non-alphanumeric titles
        if title:
            assert not all(c in string.ascii_letters + string.digits for c in title)


# Test 4: Environment required property (Name)
@given(
    name=st.text(alphabet=string.ascii_letters + string.digits, min_size=1),
    execution_role=st.text(min_size=1),
    dag_path=st.text(min_size=1)
)
def test_environment_required_properties(name, execution_role, dag_path):
    """Test that Environment enforces required Name property"""
    # Create with required property
    env = mwaa.Environment("TestEnv", Name=name)
    assert env.Name == name
    
    # Test that to_dict includes the required property
    env_dict = env.to_dict()
    assert "Properties" in env_dict
    assert "Name" in env_dict["Properties"]
    assert env_dict["Properties"]["Name"] == name


# Test 5: ModuleLoggingConfiguration property types
@given(
    enabled=st.one_of(
        st.booleans(),
        st.sampled_from([0, 1, "true", "false", "True", "False"])
    ),
    log_level=st.sampled_from(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    arn=st.text(min_size=1)
)
def test_module_logging_configuration(enabled, log_level, arn):
    """Test ModuleLoggingConfiguration accepts valid property types"""
    config = mwaa.ModuleLoggingConfiguration()
    
    # Test Enabled property with boolean validator
    if enabled in [True, 1, "1", "true", "True", False, 0, "0", "false", "False"]:
        config.Enabled = enabled
        # After setting, it should be normalized to boolean
        assert config.Enabled in [True, False]
    else:
        try:
            config.Enabled = enabled
            # Should be a boolean if it succeeds
            assert isinstance(config.Enabled, bool)
        except (ValueError, TypeError):
            pass
    
    # Test string properties
    config.LogLevel = log_level
    assert config.LogLevel == log_level
    
    config.CloudWatchLogGroupArn = arn
    assert config.CloudWatchLogGroupArn == arn


# Test 6: NetworkConfiguration with list properties
@given(
    security_groups=st.lists(st.text(alphabet=string.printable, min_size=1), min_size=0, max_size=5),
    subnets=st.lists(st.text(alphabet=string.printable, min_size=1), min_size=0, max_size=5)
)
def test_network_configuration_lists(security_groups, subnets):
    """Test NetworkConfiguration handles list properties correctly"""
    config = mwaa.NetworkConfiguration()
    
    # These should accept lists of strings
    config.SecurityGroupIds = security_groups
    assert config.SecurityGroupIds == security_groups
    
    config.SubnetIds = subnets
    assert config.SubnetIds == subnets
    
    # to_dict should preserve lists
    config_dict = config.to_dict()
    if security_groups:
        assert config_dict.get("SecurityGroupIds") == security_groups
    if subnets:
        assert config_dict.get("SubnetIds") == subnets


# Test 7: Integer properties with validators
@given(
    max_workers=st.one_of(st.integers(), st.text(), st.floats()),
    min_workers=st.one_of(st.integers(), st.text(), st.floats())
)
def test_environment_integer_properties(max_workers, min_workers):
    """Test that Environment integer properties use integer validator"""
    env = mwaa.Environment("TestEnv", Name="TestEnvironment")
    
    # Test MaxWorkers
    try:
        env.MaxWorkers = max_workers
        # If it succeeds, should be convertible to int
        assert int(env.MaxWorkers) == int(max_workers)
    except (ValueError, TypeError):
        # Should fail for non-integer values
        try:
            int(max_workers)
            # If we can convert it, the property should have accepted it
            assert False, f"MaxWorkers rejected {max_workers} but int() accepts it"
        except (ValueError, TypeError):
            pass
    
    # Test MinWorkers
    try:
        env.MinWorkers = min_workers
        # If it succeeds, should be convertible to int
        assert int(env.MinWorkers) == int(min_workers)
    except (ValueError, TypeError):
        # Should fail for non-integer values
        try:
            int(min_workers)
            assert False, f"MinWorkers rejected {min_workers} but int() accepts it"
        except (ValueError, TypeError):
            pass


# Test 8: Round-trip property for LoggingConfiguration
@given(
    dag_enabled=st.booleans(),
    dag_level=st.sampled_from(["DEBUG", "INFO", "WARNING", "ERROR"]),
    scheduler_enabled=st.booleans(),
    scheduler_level=st.sampled_from(["DEBUG", "INFO", "WARNING", "ERROR"])
)
@settings(max_examples=100)
def test_logging_configuration_roundtrip(dag_enabled, dag_level, scheduler_enabled, scheduler_level):
    """Test that LoggingConfiguration survives round-trip through dict"""
    # Create configuration with nested properties
    dag_logs = mwaa.ModuleLoggingConfiguration(
        Enabled=dag_enabled,
        LogLevel=dag_level
    )
    scheduler_logs = mwaa.ModuleLoggingConfiguration(
        Enabled=scheduler_enabled,
        LogLevel=scheduler_level
    )
    
    config = mwaa.LoggingConfiguration(
        DagProcessingLogs=dag_logs,
        SchedulerLogs=scheduler_logs
    )
    
    # Convert to dict
    config_dict = config.to_dict()
    
    # Create new object from dict
    new_config = mwaa.LoggingConfiguration.from_dict(None, config_dict)
    
    # Compare the dictionaries
    assert new_config.to_dict() == config_dict