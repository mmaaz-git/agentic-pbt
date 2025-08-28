import math
from hypothesis import assume, given, strategies as st, settings
from troposphere.ssmquicksetup import (
    ConfigurationDefinition, 
    ConfigurationManager, 
    StatusSummary
)

# Strategy for valid parameter dictionaries
params_strategy = st.dictionaries(
    st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    st.text(min_size=0, max_size=100),
    min_size=1,
    max_size=10
)

# Strategy for valid type strings 
type_strategy = st.text(min_size=1, max_size=100).filter(lambda x: x.strip())

# Strategy for optional text fields
optional_text = st.one_of(st.none(), st.text(min_size=1, max_size=100))

# Test round-trip property for ConfigurationDefinition
@given(
    params=params_strategy,
    type_str=type_strategy,
    type_version=optional_text,
    id_str=optional_text,
    local_admin_role=optional_text,
    local_exec_role=optional_text
)
def test_configuration_definition_round_trip(
    params, type_str, type_version, id_str, 
    local_admin_role, local_exec_role
):
    # Create ConfigurationDefinition
    kwargs = {
        'Parameters': params,
        'Type': type_str
    }
    if type_version is not None:
        kwargs['TypeVersion'] = type_version
    if id_str is not None:
        kwargs['id'] = id_str
    if local_admin_role is not None:
        kwargs['LocalDeploymentAdministrationRoleArn'] = local_admin_role
    if local_exec_role is not None:
        kwargs['LocalDeploymentExecutionRoleName'] = local_exec_role
    
    cd1 = ConfigurationDefinition(**kwargs)
    
    # Convert to dict and back
    dict1 = cd1.to_dict()
    cd2 = ConfigurationDefinition.from_dict('TestDef', dict1)
    dict2 = cd2.to_dict()
    
    # Should be equal
    assert dict1 == dict2


# Test round-trip property for StatusSummary
@given(
    last_updated=type_strategy,  # Using text strategy for timestamp
    status_type=type_strategy,
    status=optional_text,
    status_details=st.one_of(
        st.none(), 
        st.dictionaries(st.text(min_size=1), st.text(), max_size=5)
    ),
    status_message=optional_text
)
def test_status_summary_round_trip(
    last_updated, status_type, status, 
    status_details, status_message
):
    # Create StatusSummary
    kwargs = {
        'LastUpdatedAt': last_updated,
        'StatusType': status_type
    }
    if status is not None:
        kwargs['Status'] = status
    if status_details is not None:
        kwargs['StatusDetails'] = status_details
    if status_message is not None:
        kwargs['StatusMessage'] = status_message
    
    ss1 = StatusSummary(**kwargs)
    
    # Convert to dict and back
    dict1 = ss1.to_dict()
    ss2 = StatusSummary.from_dict('TestStatus', dict1)
    dict2 = ss2.to_dict()
    
    # Should be equal
    assert dict1 == dict2


# Test round-trip property for ConfigurationManager
@given(
    title=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    config_defs_data=st.lists(
        st.fixed_dictionaries({
            'params': params_strategy,
            'type': type_strategy,
            'type_version': optional_text,
            'id': optional_text
        }),
        min_size=1,
        max_size=5
    ),
    name=optional_text,
    description=optional_text,
    tags=st.one_of(
        st.none(),
        st.dictionaries(st.text(min_size=1), st.text(), max_size=5)
    )
)
def test_configuration_manager_round_trip(
    title, config_defs_data, name, description, tags
):
    # Create ConfigurationDefinitions
    config_defs = []
    for cd_data in config_defs_data:
        kwargs = {
            'Parameters': cd_data['params'],
            'Type': cd_data['type']
        }
        if cd_data['type_version'] is not None:
            kwargs['TypeVersion'] = cd_data['type_version']
        if cd_data['id'] is not None:
            kwargs['id'] = cd_data['id']
        config_defs.append(ConfigurationDefinition(**kwargs))
    
    # Create ConfigurationManager
    kwargs = {
        'ConfigurationDefinitions': config_defs
    }
    if name is not None:
        kwargs['Name'] = name
    if description is not None:
        kwargs['Description'] = description
    if tags is not None:
        kwargs['Tags'] = tags
    
    cm1 = ConfigurationManager(title, **kwargs)
    
    # Convert to dict - this produces CloudFormation format
    dict1 = cm1.to_dict()
    
    # Try to recreate from dict - this should work for round-trip
    # Note: from_dict expects the properties at top level, not nested under 'Properties'
    # This is the bug we're testing for
    cm2 = ConfigurationManager.from_dict(title, dict1)
    dict2 = cm2.to_dict()
    
    # Should be equal for proper round-trip
    assert dict1 == dict2


# Test that validation catches missing required fields
@given(
    has_params=st.booleans(),
    has_type=st.booleans(),
    params=params_strategy,
    type_str=type_strategy
)
def test_configuration_definition_validation(has_params, has_type, params, type_str):
    kwargs = {}
    if has_params:
        kwargs['Parameters'] = params
    if has_type:
        kwargs['Type'] = type_str
    
    if has_params and has_type:
        # Should work
        cd = ConfigurationDefinition(**kwargs)
        cd.validate()  # Should not raise
    else:
        # Should fail validation due to missing required fields
        try:
            cd = ConfigurationDefinition(**kwargs)
            cd.validate()
            # If we get here, validation didn't catch the error
            assert False, f"Validation should have failed for kwargs: {kwargs}"
        except Exception:
            # Expected behavior
            pass


if __name__ == "__main__":
    # Run the tests
    import pytest
    pytest.main([__file__, "-v"])