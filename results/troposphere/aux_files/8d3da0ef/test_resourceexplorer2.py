import troposphere.resourceexplorer2 as re2
from hypothesis import given, strategies as st, assume
import pytest


# Strategy for valid string properties
valid_strings = st.text(min_size=0, max_size=1000)

# Strategy for tag dictionaries
tag_dicts = st.dictionaries(
    keys=st.text(min_size=0, max_size=255),
    values=st.text(min_size=0, max_size=255),
    min_size=0,
    max_size=50
)

# Strategy for IncludedProperty objects
def included_property_strategy():
    return st.builds(
        re2.IncludedProperty,
        Name=valid_strings
    )

# Strategy for SearchFilter objects  
def search_filter_strategy():
    return st.builds(
        re2.SearchFilter,
        FilterString=valid_strings
    )


class TestRoundTripProperty:
    """Test round-trip property: from_dict(to_dict(x)) should equal x"""
    
    @given(filter_string=valid_strings)
    def test_searchfilter_roundtrip(self, filter_string):
        """SearchFilter should round-trip through to_dict/from_dict"""
        original = re2.SearchFilter(FilterString=filter_string)
        dict_repr = original.to_dict()
        
        # from_dict should recreate the same object
        recreated = re2.SearchFilter.from_dict('Test', dict_repr)
        recreated_dict = recreated.to_dict()
        
        assert dict_repr == recreated_dict
    
    @given(name=valid_strings)
    def test_includedproperty_roundtrip(self, name):
        """IncludedProperty should round-trip through to_dict/from_dict"""
        original = re2.IncludedProperty(Name=name)
        dict_repr = original.to_dict()
        
        # from_dict should recreate the same object
        recreated = re2.IncludedProperty.from_dict('Test', dict_repr)
        recreated_dict = recreated.to_dict()
        
        assert dict_repr == recreated_dict
    
    @given(view_arn=valid_strings)
    def test_defaultviewassociation_roundtrip(self, view_arn):
        """DefaultViewAssociation to_dict/from_dict round-trip should work"""
        original = re2.DefaultViewAssociation('TestDVA', ViewArn=view_arn)
        dict_repr = original.to_dict()
        
        # from_dict expects the dict without the Properties wrapper
        # This tests if from_dict can handle the output of to_dict
        try:
            recreated = re2.DefaultViewAssociation.from_dict('TestDVA', dict_repr)
            recreated_dict = recreated.to_dict()
            assert dict_repr == recreated_dict
        except ValueError as e:
            if "does not have a Properties property" in str(e):
                # This is the bug - from_dict cannot handle to_dict output
                # Try with just the properties
                if 'Properties' in dict_repr:
                    recreated = re2.DefaultViewAssociation.from_dict('TestDVA', dict_repr['Properties'])
                    recreated_dict = recreated.to_dict()
                    # The round-trip fails because formats don't match
                    assert False, f"Round-trip fails: to_dict returns {dict_repr} but from_dict expects {dict_repr.get('Properties')}"
            else:
                raise
    
    @given(type_value=valid_strings, tags=tag_dicts)
    def test_index_roundtrip(self, type_value, tags):
        """Index to_dict/from_dict round-trip should work"""
        kwargs = {'Type': type_value}
        if tags:
            kwargs['Tags'] = tags
            
        original = re2.Index('TestIndex', **kwargs)
        dict_repr = original.to_dict()
        
        # from_dict expects the dict without the Properties wrapper  
        # This tests if from_dict can handle the output of to_dict
        try:
            recreated = re2.Index.from_dict('TestIndex', dict_repr)
            recreated_dict = recreated.to_dict()
            assert dict_repr == recreated_dict
        except ValueError as e:
            if "does not have a Properties property" in str(e):
                # This is the bug - from_dict cannot handle to_dict output
                if 'Properties' in dict_repr:
                    recreated = re2.Index.from_dict('TestIndex', dict_repr['Properties'])
                    recreated_dict = recreated.to_dict()
                    # The round-trip fails because formats don't match
                    assert False, f"Round-trip fails: to_dict returns {dict_repr} but from_dict expects {dict_repr.get('Properties')}"
            else:
                raise
    
    @given(
        view_name=valid_strings,
        scope=st.one_of(st.none(), valid_strings),
        tags=st.one_of(st.none(), tag_dicts),
        filters=st.one_of(st.none(), search_filter_strategy()),
        included_properties=st.one_of(st.none(), st.lists(included_property_strategy(), min_size=0, max_size=10))
    )
    def test_view_roundtrip(self, view_name, scope, tags, filters, included_properties):
        """View to_dict/from_dict round-trip should work"""
        kwargs = {'ViewName': view_name}
        if scope is not None:
            kwargs['Scope'] = scope
        if tags is not None:
            kwargs['Tags'] = tags
        if filters is not None:
            kwargs['Filters'] = filters
        if included_properties is not None:
            kwargs['IncludedProperties'] = included_properties
            
        original = re2.View('TestView', **kwargs)
        dict_repr = original.to_dict()
        
        # from_dict expects the dict without the Properties wrapper
        # This tests if from_dict can handle the output of to_dict
        try:
            recreated = re2.View.from_dict('TestView', dict_repr)
            recreated_dict = recreated.to_dict()
            assert dict_repr == recreated_dict
        except ValueError as e:
            if "does not have a Properties property" in str(e):
                # This is the bug - from_dict cannot handle to_dict output
                if 'Properties' in dict_repr:
                    recreated = re2.View.from_dict('TestView', dict_repr['Properties'])
                    recreated_dict = recreated.to_dict()
                    # The round-trip fails because formats don't match
                    assert False, f"Round-trip fails: to_dict output has Properties wrapper but from_dict doesn't expect it"
            else:
                raise


class TestTypeValidation:
    """Test that type validation works correctly"""
    
    @given(value=st.one_of(st.integers(), st.floats(), st.lists(st.text()), st.dictionaries(st.text(), st.text())))
    def test_view_viewname_requires_string(self, value):
        """View.ViewName should only accept strings"""
        if isinstance(value, str):
            # Should succeed with string
            view = re2.View('Test', ViewName=value)
            assert view.to_dict()['Properties']['ViewName'] == value
        else:
            # Should fail with non-string
            with pytest.raises(TypeError):
                re2.View('Test', ViewName=value)
    
    @given(value=st.one_of(st.integers(), st.floats(), st.lists(st.text()), st.text()))
    def test_view_tags_requires_dict(self, value):
        """View.Tags should only accept dicts"""
        if isinstance(value, dict):
            # Should succeed with dict
            view = re2.View('Test', ViewName='test', Tags=value)
            assert view.to_dict()['Properties'].get('Tags') == value
        else:
            # Should fail with non-dict
            with pytest.raises(TypeError):
                re2.View('Test', ViewName='test', Tags=value)


class TestListProperties:
    """Test list property handling"""
    
    @given(included_props=st.lists(included_property_strategy(), min_size=0, max_size=100))
    def test_view_includedproperties_list(self, included_props):
        """View.IncludedProperties should handle lists correctly"""
        view = re2.View('Test', ViewName='test', IncludedProperties=included_props)
        result = view.to_dict()
        
        if included_props:
            assert 'IncludedProperties' in result['Properties']
            assert len(result['Properties']['IncludedProperties']) == len(included_props)
            # Check each item is serialized correctly
            for i, prop in enumerate(included_props):
                assert result['Properties']['IncludedProperties'][i] == prop.to_dict()
        else:
            # Empty list might be omitted or included
            if 'IncludedProperties' in result['Properties']:
                assert result['Properties']['IncludedProperties'] == []
    
    @given(invalid_items=st.lists(
        st.one_of(st.text(), st.integers(), st.none(), st.dictionaries(st.text(), st.text())),
        min_size=1,
        max_size=10
    ))
    def test_view_includedproperties_type_checking(self, invalid_items):
        """View.IncludedProperties should reject non-IncludedProperty items"""
        with pytest.raises(TypeError):
            re2.View('Test', ViewName='test', IncludedProperties=invalid_items)


class TestDictProperties:
    """Test dict property handling"""
    
    @given(tags=tag_dicts)
    def test_view_tags_dict(self, tags):
        """View.Tags should handle dicts correctly"""
        view = re2.View('Test', ViewName='test', Tags=tags)
        result = view.to_dict()
        
        if tags:
            assert 'Tags' in result['Properties']
            assert result['Properties']['Tags'] == tags
        else:
            # Empty dict might be omitted or included
            if 'Tags' in result['Properties']:
                assert result['Properties']['Tags'] == {}
    
    @given(tags=tag_dicts)
    def test_index_tags_dict(self, tags):
        """Index.Tags should handle dicts correctly"""
        index = re2.Index('Test', Type='LOCAL', Tags=tags)
        result = index.to_dict()
        
        if tags:
            assert 'Tags' in result['Properties']
            assert result['Properties']['Tags'] == tags
        else:
            # Empty dict might be omitted or included
            if 'Tags' in result['Properties']:
                assert result['Properties']['Tags'] == {}