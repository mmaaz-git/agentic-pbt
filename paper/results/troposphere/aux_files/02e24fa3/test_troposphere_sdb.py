import troposphere.sdb
from hypothesis import given, strategies as st


@given(
    title=st.text(min_size=1),
    description=st.text()
)
def test_domain_round_trip_properties_only(title, description):
    """Test that Domain objects can round-trip through to_dict/from_dict when using Properties key"""
    original = troposphere.sdb.Domain(title, Description=description)
    dict_repr = original.to_dict()
    
    # from_dict expects just the properties, not the full structure
    restored = troposphere.sdb.Domain.from_dict(title, dict_repr['Properties'])
    restored_dict = restored.to_dict()
    
    assert dict_repr == restored_dict
    assert restored.title == original.title


@given(
    title=st.text(min_size=1),
    description=st.text()
)
def test_domain_round_trip_full_dict(title, description):
    """Test that Domain objects can round-trip through to_dict/from_dict with full dict"""
    original = troposphere.sdb.Domain(title, Description=description)
    dict_repr = original.to_dict()
    
    # This should work but doesn't - from_dict should handle the full to_dict output
    restored = troposphere.sdb.Domain.from_dict(title, dict_repr)
    restored_dict = restored.to_dict()
    
    assert dict_repr == restored_dict
    assert restored.title == original.title


@given(
    title=st.text(min_size=1),
    description=st.text()
)
def test_domain_to_dict_consistency(title, description):
    """Test that to_dict produces consistent output for same inputs"""
    domain1 = troposphere.sdb.Domain(title, Description=description)
    domain2 = troposphere.sdb.Domain(title, Description=description)
    
    assert domain1.to_dict() == domain2.to_dict()


@given(
    title=st.text(min_size=1)
)
def test_domain_creation_without_description(title):
    """Test that Domain can be created without optional Description"""
    domain = troposphere.sdb.Domain(title)
    dict_repr = domain.to_dict()
    
    assert 'Type' in dict_repr
    assert dict_repr['Type'] == 'AWS::SDB::Domain'
    # Properties should be empty or not have Description
    if 'Properties' in dict_repr:
        assert 'Description' not in dict_repr['Properties'] or dict_repr['Properties']['Description'] == ''