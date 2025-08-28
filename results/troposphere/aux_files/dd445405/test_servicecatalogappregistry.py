"""Property-based tests for troposphere.servicecatalogappregistry module"""

import pytest
from hypothesis import given, strategies as st, assume
import troposphere.servicecatalogappregistry as module


# Strategy for valid names (non-empty strings)
valid_name = st.text(min_size=1, max_size=100)

# Strategy for descriptions
descriptions = st.text(max_size=200)

# Strategy for tags (dict with string keys and values)
tag_strategy = st.dictionaries(
    st.text(min_size=1, max_size=50),
    st.text(max_size=100),
    max_size=10
)

# Strategy for attribute dicts
attribute_strategy = st.dictionaries(
    st.text(min_size=1, max_size=50),
    st.one_of(
        st.text(),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.booleans()
    ),
    min_size=1,  # Required field, must have at least one item
    max_size=10
)


@given(
    name=valid_name,
    description=st.one_of(st.none(), descriptions),
    tags=st.one_of(st.none(), tag_strategy)
)
def test_application_round_trip(name, description, tags):
    """Test that Application to_dict -> from_dict preserves properties"""
    # Create application with optional fields
    kwargs = {'Name': name}
    if description is not None:
        kwargs['Description'] = description
    if tags is not None:
        kwargs['Tags'] = tags
    
    app1 = module.Application('TestApp', **kwargs)
    
    # Convert to dict and back
    dict1 = app1.to_dict()
    props = dict1['Properties']
    app2 = module.Application.from_dict('TestApp2', props)
    dict2 = app2.to_dict()
    
    # Properties should be preserved
    assert dict1['Properties'] == dict2['Properties']
    assert dict1['Type'] == dict2['Type']


@given(
    name=valid_name,
    attributes=attribute_strategy,
    description=st.one_of(st.none(), descriptions),
    tags=st.one_of(st.none(), tag_strategy)
)
def test_attributegroup_round_trip(name, attributes, description, tags):
    """Test that AttributeGroup to_dict -> from_dict preserves properties"""
    kwargs = {'Name': name, 'Attributes': attributes}
    if description is not None:
        kwargs['Description'] = description
    if tags is not None:
        kwargs['Tags'] = tags
    
    ag1 = module.AttributeGroup('TestAG', **kwargs)
    
    # Convert to dict and back
    dict1 = ag1.to_dict()
    props = dict1['Properties']
    ag2 = module.AttributeGroup.from_dict('TestAG2', props)
    dict2 = ag2.to_dict()
    
    # Properties should be preserved
    assert dict1['Properties'] == dict2['Properties']
    assert dict1['Type'] == dict2['Type']


@given(st.text())  # Any string, including empty
def test_application_empty_string_validation(name_value):
    """Test that Application Name field validation handles empty strings correctly"""
    app = module.Application('TestApp', Name=name_value)
    
    if name_value == '':
        # Empty string should arguably be invalid for a required Name field
        # but the implementation accepts it
        result = app.to_dict()
        assert result['Properties']['Name'] == ''
    else:
        result = app.to_dict()
        assert result['Properties']['Name'] == name_value


@given(
    app_name=valid_name,
    attr_group_name=valid_name
)
def test_association_string_validation(app_name, attr_group_name):
    """Test that association classes validate string fields correctly"""
    # AttributeGroupAssociation requires Application and AttributeGroup as strings
    aga = module.AttributeGroupAssociation(
        'TestAGA',
        Application=app_name,
        AttributeGroup=attr_group_name
    )
    
    result = aga.to_dict()
    assert result['Properties']['Application'] == app_name
    assert result['Properties']['AttributeGroup'] == attr_group_name
    
    # ResourceAssociation requires Application, Resource, and ResourceType as strings
    ra = module.ResourceAssociation(
        'TestRA',
        Application=app_name,
        Resource='arn:aws:resource',
        ResourceType='CFN_STACK'
    )
    
    result = ra.to_dict()
    assert result['Properties']['Application'] == app_name


@given(
    name=valid_name,
    invalid_type=st.one_of(
        st.integers(),
        st.floats(),
        st.lists(st.text()),
        st.dictionaries(st.text(), st.text())
    )
)
def test_type_validation_consistency(name, invalid_type):
    """Test that type validation is consistent across different fields"""
    # Test Application with invalid Name type
    with pytest.raises(TypeError, match="expected <class 'str'>"):
        app = module.Application('TestApp', Name=invalid_type)
        app.to_dict()
    
    # Test Application with invalid Description type (when not None)
    with pytest.raises(TypeError, match="expected <class 'str'>"):
        app = module.Application('TestApp', Name=name, Description=invalid_type)
        app.to_dict()


@given(
    name=valid_name,
    tags=st.one_of(
        st.text(),  # Should be dict, not string
        st.integers(),
        st.lists(st.text())
    )
)
def test_tags_must_be_dict(name, tags):
    """Test that Tags field requires dict type"""
    with pytest.raises(TypeError, match="expected <class 'dict'>"):
        app = module.Application('TestApp', Name=name, Tags=tags)
        app.to_dict()


@given(st.data())
def test_complex_nested_attributes(data):
    """Test that AttributeGroup handles complex nested attribute structures"""
    # Generate complex nested structure
    def make_nested_dict(depth=0, max_depth=3):
        if depth >= max_depth:
            return data.draw(st.one_of(
                st.text(),
                st.integers(),
                st.floats(allow_nan=False, allow_infinity=False),
                st.booleans()
            ))
        return data.draw(st.dictionaries(
            st.text(min_size=1, max_size=20),
            st.one_of(
                st.text(),
                st.integers(),
                st.floats(allow_nan=False, allow_infinity=False),
                st.booleans(),
                st.builds(lambda: make_nested_dict(depth + 1, max_depth))
            ),
            min_size=1 if depth == 0 else 0,
            max_size=5
        ))
    
    attributes = make_nested_dict()
    name = data.draw(valid_name)
    
    ag = module.AttributeGroup('TestAG', Name=name, Attributes=attributes)
    result = ag.to_dict()
    
    # Should preserve the complex structure
    assert result['Properties']['Attributes'] == attributes
    
    # Round-trip should work
    ag2 = module.AttributeGroup.from_dict('TestAG2', result['Properties'])
    result2 = ag2.to_dict()
    assert result2['Properties']['Attributes'] == attributes