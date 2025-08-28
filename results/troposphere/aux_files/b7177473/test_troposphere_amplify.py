#!/usr/bin/env python3
"""Property-based tests for troposphere.amplify module."""

import json
import math
from hypothesis import given, strategies as st, settings, assume, example
import pytest

# Import the modules to test
from troposphere import AWSObject, AWSProperty
from troposphere.validators import boolean
from troposphere.amplify import (
    App, Branch, Domain, 
    BasicAuthConfig, EnvironmentVariable,
    AutoBranchCreationConfig, CustomRule,
    SubDomainSetting, CertificateSettings
)


# Test 1: Boolean validator idempotence and consistency
@given(st.one_of(
    st.booleans(),
    st.integers(min_value=0, max_value=1),
    st.sampled_from(["0", "1", "true", "false", "True", "False"])
))
def test_boolean_validator_idempotence(value):
    """The boolean validator should be idempotent - applying it twice should give the same result."""
    try:
        result1 = boolean(value)
        result2 = boolean(result1)
        assert result1 == result2
        assert isinstance(result1, bool)
        assert isinstance(result2, bool)
    except ValueError:
        # Some values are expected to raise ValueError
        pass


@given(st.one_of(
    st.sampled_from([True, 1, "1", "true", "True"]),
    st.sampled_from([False, 0, "0", "false", "False"])
))
def test_boolean_validator_valid_inputs(value):
    """Boolean validator should convert all documented true/false values correctly."""
    result = boolean(value)
    assert isinstance(result, bool)
    
    # Check that true-like values return True
    if value in [True, 1, "1", "true", "True"]:
        assert result is True
    # Check that false-like values return False
    elif value in [False, 0, "0", "false", "False"]:
        assert result is False


@given(st.one_of(
    st.integers().filter(lambda x: x not in [0, 1]),
    st.text().filter(lambda x: x not in ["0", "1", "true", "false", "True", "False"]),
    st.floats(),
    st.none()
))
def test_boolean_validator_invalid_inputs(value):
    """Boolean validator should raise ValueError for invalid inputs."""
    with pytest.raises(ValueError):
        boolean(value)


# Test 2: Required property validation
@given(st.text(min_size=1, max_size=100).filter(lambda x: x.replace("_", "").replace("-", "").isalnum()))
def test_app_required_name_property(name):
    """App objects require a Name property."""
    # Should succeed with required Name property
    app = App('TestApp', Name=name)
    assert app.properties['Name'] == name
    
    # to_dict should include the Name
    app_dict = app.to_dict()
    assert 'Properties' in app_dict
    assert 'Name' in app_dict['Properties']
    assert app_dict['Properties']['Name'] == name


def test_app_missing_required_property():
    """App should fail validation when required Name property is missing."""
    app = App('TestApp')
    with pytest.raises(ValueError, match="Resource TestApp required property Name not set"):
        app.to_dict()


@given(
    st.text(min_size=1, max_size=100),
    st.text(min_size=1, max_size=100)
)
def test_environment_variable_required_properties(name, value):
    """EnvironmentVariable requires both Name and Value properties."""
    env_var = EnvironmentVariable(Name=name, Value=value)
    assert env_var.properties['Name'] == name
    assert env_var.properties['Value'] == value
    
    # Check serialization
    env_dict = env_var.to_dict()
    assert env_dict['Name'] == name
    assert env_dict['Value'] == value


# Test 3: Type validation
@given(st.one_of(
    st.integers(),
    st.floats(),
    st.lists(st.text()),
    st.dictionaries(st.text(), st.text())
))
def test_app_name_type_validation(invalid_name):
    """App Name property should only accept strings."""
    assume(not isinstance(invalid_name, str))
    
    app = App('TestApp')
    with pytest.raises(TypeError, match="Name is .*, expected <class 'str'>"):
        app.Name = invalid_name


@given(st.lists(st.text()))
def test_custom_rules_list_validation(texts):
    """CustomRules property should only accept a list of CustomRule objects."""
    app = App('TestApp', Name='Test')
    
    # Should fail with list of strings
    with pytest.raises(TypeError):
        app.CustomRules = texts


# Test 4: Round-trip serialization
@given(
    st.text(min_size=1, max_size=50).filter(lambda x: x.isalnum()),
    st.text(min_size=1, max_size=100),
    st.text(min_size=0, max_size=200),
    st.text(min_size=0, max_size=100)
)
def test_app_round_trip_serialization(title, name, description, platform):
    """App serialization to_dict and from_dict should be inverses."""
    # Create an App with various properties
    app1 = App(
        title,
        Name=name,
        Description=description if description else None,
        Platform=platform if platform else None
    )
    
    # Convert to dict
    app_dict = app1.to_dict()
    
    # Extract properties for from_dict
    props = app_dict.get('Properties', {})
    
    # Create new App from dict
    app2 = App._from_dict(title, **props)
    
    # Compare the two apps
    assert app2.title == app1.title
    assert app2.properties == app1.properties
    assert app2.to_dict() == app1.to_dict()


@given(
    st.text(min_size=1, max_size=100),
    st.text(min_size=1, max_size=100)
)
def test_environment_variable_round_trip(name, value):
    """EnvironmentVariable round-trip serialization."""
    env1 = EnvironmentVariable(Name=name, Value=value)
    env_dict = env1.to_dict()
    
    env2 = EnvironmentVariable._from_dict(**env_dict)
    
    assert env2.properties == env1.properties
    assert env2.to_dict() == env1.to_dict()


# Test 5: Nested property validation
@given(
    st.text(min_size=1, max_size=50),
    st.text(min_size=1, max_size=50),
    st.booleans()
)
def test_basic_auth_config_validation(username, password, enable):
    """BasicAuthConfig should validate its properties correctly."""
    config = BasicAuthConfig(
        Username=username,
        Password=password,
        EnableBasicAuth=enable
    )
    
    assert config.properties['Username'] == username
    assert config.properties['Password'] == password
    assert config.properties['EnableBasicAuth'] == enable
    
    # Check that boolean conversion happened
    assert isinstance(config.properties['EnableBasicAuth'], bool)


@given(
    st.lists(
        st.fixed_dictionaries({
            'Name': st.text(min_size=1, max_size=50),
            'Value': st.text(min_size=1, max_size=100)
        }),
        min_size=0,
        max_size=10
    )
)
def test_app_environment_variables_list(env_vars_data):
    """App should accept a list of EnvironmentVariable objects."""
    env_vars = [EnvironmentVariable(**data) for data in env_vars_data]
    
    app = App('TestApp', Name='Test', EnvironmentVariables=env_vars)
    
    assert len(app.properties.get('EnvironmentVariables', [])) == len(env_vars)
    
    # Check serialization
    app_dict = app.to_dict()
    if env_vars:
        assert 'EnvironmentVariables' in app_dict['Properties']
        assert len(app_dict['Properties']['EnvironmentVariables']) == len(env_vars)


# Test 6: Custom rule validation
@given(
    st.text(min_size=1, max_size=100),
    st.text(min_size=1, max_size=100),
    st.text(min_size=0, max_size=100),
    st.text(min_size=0, max_size=20)
)
def test_custom_rule_properties(source, target, condition, status):
    """CustomRule should validate required Source and Target properties."""
    rule = CustomRule(
        Source=source,
        Target=target,
        Condition=condition if condition else None,
        Status=status if status else None
    )
    
    assert rule.properties['Source'] == source
    assert rule.properties['Target'] == target
    
    # Optional properties
    if condition:
        assert rule.properties['Condition'] == condition
    if status:
        assert rule.properties['Status'] == status


# Test 7: SubDomainSetting validation
@given(
    st.text(min_size=1, max_size=50),
    st.text(min_size=1, max_size=50)
)
def test_subdomain_setting_required_properties(branch_name, prefix):
    """SubDomainSetting requires BranchName and Prefix."""
    setting = SubDomainSetting(
        BranchName=branch_name,
        Prefix=prefix
    )
    
    assert setting.properties['BranchName'] == branch_name
    assert setting.properties['Prefix'] == prefix
    
    # Check serialization
    setting_dict = setting.to_dict()
    assert setting_dict['BranchName'] == branch_name
    assert setting_dict['Prefix'] == prefix


# Test 8: Title validation
@given(st.text(min_size=1).filter(lambda x: not x.replace("_", "").replace("-", "").isalnum() or not x))
def test_invalid_title_validation(invalid_title):
    """AWS resources should reject non-alphanumeric titles."""
    assume(not valid_names.match(invalid_title))
    
    with pytest.raises(ValueError, match='Name ".*" not alphanumeric'):
        App(invalid_title, Name='Test')


import re
valid_names = re.compile(r"^[a-zA-Z0-9]+$")


# Test 9: Property assignment after creation
@given(
    st.text(min_size=1, max_size=100),
    st.text(min_size=1, max_size=200)
)
def test_property_assignment_after_creation(name1, name2):
    """Properties can be assigned after object creation."""
    app = App('TestApp')
    
    # Assign Name property
    app.Name = name1
    assert app.properties['Name'] == name1
    
    # Reassign to different value
    app.Name = name2
    assert app.properties['Name'] == name2
    
    # Should validate successfully now
    app_dict = app.to_dict()
    assert app_dict['Properties']['Name'] == name2


# Test 10: List property type enforcement
def test_environment_variables_type_enforcement():
    """EnvironmentVariables property should enforce list of EnvironmentVariable objects."""
    app = App('TestApp', Name='Test')
    
    # Should accept empty list
    app.EnvironmentVariables = []
    assert app.properties['EnvironmentVariables'] == []
    
    # Should accept list of EnvironmentVariable objects
    env_vars = [
        EnvironmentVariable(Name='KEY1', Value='VALUE1'),
        EnvironmentVariable(Name='KEY2', Value='VALUE2')
    ]
    app.EnvironmentVariables = env_vars
    assert len(app.properties['EnvironmentVariables']) == 2
    
    # Should reject non-list
    with pytest.raises(TypeError):
        app.EnvironmentVariables = "not a list"
    
    # Should reject list of wrong type
    with pytest.raises(TypeError):
        app.EnvironmentVariables = ["string1", "string2"]


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])