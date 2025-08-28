"""Extended property-based testing with more examples"""

import pytest
from hypothesis import given, strategies as st, settings
import troposphere.resourcegroups as rg


# Test with more examples to find edge cases
@settings(max_examples=1000)
@given(st.text())
def test_resourcequery_type_validator_comprehensive(value):
    """
    Property: resourcequery_type should only accept TAG_FILTERS_1_0 or 
    CLOUDFORMATION_STACK_1_0, return them unchanged, or raise ValueError.
    """
    valid_types = ["TAG_FILTERS_1_0", "CLOUDFORMATION_STACK_1_0"]
    
    if value in valid_types:
        result = rg.resourcequery_type(value)
        assert result == value
    else:
        with pytest.raises(ValueError) as exc_info:
            rg.resourcequery_type(value)
        assert 'Type must be one of' in str(exc_info.value)


# Test edge cases with special strings
@given(
    st.one_of(
        st.just(""),  # empty string
        st.just(" TAG_FILTERS_1_0"),  # leading space
        st.just("TAG_FILTERS_1_0 "),  # trailing space
        st.just("tag_filters_1_0"),  # lowercase
        st.just("TAG_FILTERS_1_0\n"),  # with newline
        st.just("TAG_FILTERS_1_0\x00"),  # with null byte
        st.text(alphabet="TAG_FILTERS10", min_size=1)  # permutations
    )
)
def test_resourcequery_type_edge_cases(value):
    """Test edge cases for resourcequery_type validator"""
    valid_types = ["TAG_FILTERS_1_0", "CLOUDFORMATION_STACK_1_0"]
    
    if value in valid_types:
        result = rg.resourcequery_type(value)
        assert result == value
    else:
        with pytest.raises(ValueError):
            rg.resourcequery_type(value)


# Test with Unicode and special characters
@settings(max_examples=500)
@given(
    name=st.one_of(
        st.text(min_size=1),
        st.text(alphabet="🦄🔥💎", min_size=1, max_size=5),  # emojis
        st.text(alphabet="\x00\x01\x02", min_size=1, max_size=3),  # control chars
    ),
    values=st.lists(st.text(), max_size=5)
)
def test_configuration_parameter_unicode(name, values):
    """Test ConfigurationParameter with various Unicode inputs"""
    cp = rg.ConfigurationParameter(Name=name, Values=values)
    dict_repr = cp.to_dict()
    
    assert dict_repr['Name'] == name
    assert dict_repr['Values'] == values
    
    # Round-trip
    cp2 = rg.ConfigurationParameter.from_dict('Test', dict_repr)
    assert cp2.to_dict() == dict_repr


# Test large nested structures
@settings(max_examples=100)
@given(
    params=st.lists(
        st.builds(
            rg.ConfigurationParameter,
            Name=st.text(min_size=1, max_size=1000),  # long names
            Values=st.lists(st.text(max_size=1000), min_size=0, max_size=100)  # many values
        ),
        min_size=0,
        max_size=50  # many parameters
    )
)
def test_configuration_item_scale(params):
    """Test ConfigurationItem with large/many nested structures"""
    item = rg.ConfigurationItem(Parameters=params, Type="TestType")
    dict_repr = item.to_dict()
    
    assert len(dict_repr['Parameters']) == len(params)
    
    # Verify each parameter
    for i, param_dict in enumerate(dict_repr['Parameters']):
        assert param_dict == params[i].to_dict()


# Test with None and empty values systematically
@given(
    key=st.one_of(st.none(), st.just(""), st.text(min_size=1)),
    values=st.one_of(
        st.none(),
        st.just([]),
        st.lists(st.one_of(st.none(), st.just(""), st.text()), max_size=5)
    )
)
def test_tag_filter_none_empty(key, values):
    """Test TagFilter with None and empty values"""
    kwargs = {}
    if key is not None:
        kwargs['Key'] = key
    if values is not None:
        kwargs['Values'] = values
    
    tf = rg.TagFilter(**kwargs)
    dict_repr = tf.to_dict()
    
    if key is not None:
        assert dict_repr.get('Key') == key
    else:
        assert 'Key' not in dict_repr
        
    if values is not None:
        assert dict_repr.get('Values') == values
    else:
        assert 'Values' not in dict_repr