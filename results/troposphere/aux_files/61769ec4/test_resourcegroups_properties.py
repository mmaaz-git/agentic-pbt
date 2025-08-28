"""Property-based testing for troposphere.resourcegroups module"""

import pytest
from hypothesis import given, strategies as st, assume, settings
import troposphere.resourcegroups as rg


# Test 1: resourcequery_type validator invariant
@given(st.text())
def test_resourcequery_type_validator_invariant(value):
    """
    Property: resourcequery_type should only accept TAG_FILTERS_1_0 or 
    CLOUDFORMATION_STACK_1_0, return them unchanged, or raise ValueError.
    """
    valid_types = ["TAG_FILTERS_1_0", "CLOUDFORMATION_STACK_1_0"]
    
    if value in valid_types:
        # Should return the value unchanged
        result = rg.resourcequery_type(value)
        assert result == value
    else:
        # Should raise ValueError
        with pytest.raises(ValueError) as exc_info:
            rg.resourcequery_type(value)
        assert 'Type must be one of' in str(exc_info.value)


# Test 2: Round-trip property for Query objects
@given(
    resource_type_filters=st.lists(st.text(min_size=1), max_size=10),
    stack_identifier=st.text(min_size=1),
    tag_filters=st.lists(
        st.builds(
            rg.TagFilter,
            Key=st.text(min_size=1),
            Values=st.lists(st.text(min_size=1), min_size=1, max_size=5)
        ),
        max_size=5
    )
)
def test_query_round_trip_property(resource_type_filters, stack_identifier, tag_filters):
    """
    Property: Query objects should survive to_dict/from_dict round-trip
    """
    # Create Query with all fields
    query = rg.Query(
        ResourceTypeFilters=resource_type_filters,
        StackIdentifier=stack_identifier,
        TagFilters=tag_filters
    )
    
    # Convert to dict and back
    dict_repr = query.to_dict()
    query_recreated = rg.Query.from_dict('TestQuery', dict_repr)
    dict_repr2 = query_recreated.to_dict()
    
    # Should be identical
    assert dict_repr == dict_repr2


# Test 3: Empty fields behavior in to_dict
@given(
    include_name=st.booleans(),
    name_value=st.text() if True else st.none(),
    include_values=st.booleans(),
    values_list=st.lists(st.text(), max_size=5) if True else st.none()
)
def test_configuration_parameter_empty_fields(include_name, name_value, include_values, values_list):
    """
    Property: Empty/None fields should not appear in to_dict() output
    """
    kwargs = {}
    if include_name and name_value is not None:
        kwargs['Name'] = name_value
    if include_values and values_list is not None:
        kwargs['Values'] = values_list
    
    cp = rg.ConfigurationParameter(**kwargs)
    result = cp.to_dict()
    
    # Check that only set fields appear
    if include_name and name_value is not None:
        assert 'Name' in result
        assert result['Name'] == name_value
    else:
        assert 'Name' not in result
    
    if include_values and values_list is not None:
        assert 'Values' in result
        assert result['Values'] == values_list
    else:
        assert 'Values' not in result


# Test 4: ResourceQuery Type validation
@given(
    type_value=st.one_of(
        st.sampled_from(["TAG_FILTERS_1_0", "CLOUDFORMATION_STACK_1_0"]),
        st.text()
    ),
    include_query=st.booleans()
)
def test_resource_query_type_validation(type_value, include_query):
    """
    Property: ResourceQuery should validate Type field using resourcequery_type
    """
    valid_types = ["TAG_FILTERS_1_0", "CLOUDFORMATION_STACK_1_0"]
    
    kwargs = {'Type': type_value}
    if include_query:
        kwargs['Query'] = rg.Query()
    
    if type_value in valid_types:
        # Should succeed
        rq = rg.ResourceQuery(**kwargs)
        assert rq.to_dict()['Type'] == type_value
    else:
        # Should fail validation
        with pytest.raises(ValueError) as exc_info:
            rg.ResourceQuery(**kwargs)
        assert 'Type must be one of' in str(exc_info.value)


# Test 5: Group object with required and optional fields
@given(
    title=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=50),
    name=st.text(min_size=1),
    description=st.one_of(st.none(), st.text()),
    resources=st.one_of(st.none(), st.lists(st.text(min_size=1), max_size=5))
)
def test_group_object_creation(title, name, description, resources):
    """
    Property: Group objects should handle required (Name) and optional fields correctly
    """
    kwargs = {'Name': name}
    if description is not None:
        kwargs['Description'] = description
    if resources is not None:
        kwargs['Resources'] = resources
    
    group = rg.Group(title, **kwargs)
    
    # Check required fields
    assert group.title == title
    assert group.resource_type == "AWS::ResourceGroups::Group"
    
    dict_repr = group.to_dict()
    # AWSObject wraps properties in 'Properties' key
    assert 'Properties' in dict_repr
    assert 'Type' in dict_repr
    assert dict_repr['Type'] == "AWS::ResourceGroups::Group"
    
    props = dict_repr['Properties']
    assert props['Name'] == name
    
    # Check optional fields
    if description is not None:
        assert props.get('Description') == description
    else:
        assert 'Description' not in props
    
    if resources is not None:
        assert props.get('Resources') == resources
    else:
        assert 'Resources' not in props


# Test 6: TagSyncTask required fields
@given(
    title=st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=50),
    group=st.text(min_size=1),
    role_arn=st.text(min_size=1),
    tag_key=st.text(min_size=1),
    tag_value=st.text(min_size=1)
)
def test_tag_sync_task_required_fields(title, group, role_arn, tag_key, tag_value):
    """
    Property: TagSyncTask should require all its fields (Group, RoleArn, TagKey, TagValue)
    """
    task = rg.TagSyncTask(
        title,
        Group=group,
        RoleArn=role_arn,
        TagKey=tag_key,
        TagValue=tag_value
    )
    
    assert task.title == title
    assert task.resource_type == "AWS::ResourceGroups::TagSyncTask"
    
    dict_repr = task.to_dict()
    # AWSObject wraps properties in 'Properties' key
    assert 'Properties' in dict_repr
    assert 'Type' in dict_repr
    assert dict_repr['Type'] == "AWS::ResourceGroups::TagSyncTask"
    
    props = dict_repr['Properties']
    assert props['Group'] == group
    assert props['RoleArn'] == role_arn
    assert props['TagKey'] == tag_key
    assert props['TagValue'] == tag_value


# Test 7: Complex nested structure round-trip
@given(
    params=st.lists(
        st.builds(
            rg.ConfigurationParameter,
            Name=st.text(min_size=1),
            Values=st.lists(st.text(min_size=1), min_size=1, max_size=3)
        ),
        min_size=1,
        max_size=3
    ),
    type_value=st.text(min_size=1)
)
def test_configuration_item_nested_round_trip(params, type_value):
    """
    Property: ConfigurationItem with nested ConfigurationParameters should round-trip correctly
    """
    item = rg.ConfigurationItem(
        Parameters=params,
        Type=type_value
    )
    
    dict_repr = item.to_dict()
    
    # Verify structure
    assert 'Parameters' in dict_repr
    assert 'Type' in dict_repr
    assert dict_repr['Type'] == type_value
    assert len(dict_repr['Parameters']) == len(params)
    
    # Each parameter should be serialized correctly
    for i, param_dict in enumerate(dict_repr['Parameters']):
        original_param_dict = params[i].to_dict()
        assert param_dict == original_param_dict
    
    # Test from_dict
    item_recreated = rg.ConfigurationItem.from_dict('TestItem', dict_repr)
    dict_repr2 = item_recreated.to_dict()
    assert dict_repr == dict_repr2


# Test 8: Edge case - empty lists vs None
@given(
    use_empty_list=st.booleans(),
    use_none=st.booleans()
)
def test_query_empty_list_vs_none(use_empty_list, use_none):
    """
    Property: Empty lists should be preserved in to_dict, None values should not appear
    """
    if use_empty_list:
        query = rg.Query(ResourceTypeFilters=[])
        dict_repr = query.to_dict()
        assert 'ResourceTypeFilters' in dict_repr
        assert dict_repr['ResourceTypeFilters'] == []
    elif use_none:
        # Don't set the field at all
        query = rg.Query()
        dict_repr = query.to_dict()
        assert 'ResourceTypeFilters' not in dict_repr
    else:
        # Set with actual values
        query = rg.Query(ResourceTypeFilters=['AWS::EC2::Instance'])
        dict_repr = query.to_dict()
        assert dict_repr['ResourceTypeFilters'] == ['AWS::EC2::Instance']