import pytest
from hypothesis import given, strategies as st, assume, settings
import troposphere.emrcontainers as emr
import troposphere


# Strategy for valid namespace strings
namespace_strategy = st.text(min_size=1, max_size=100).filter(
    lambda x: x.strip() != '' and not any(c in x for c in ['\x00', '\n', '\r'])
)

# Strategy for valid IDs
id_strategy = st.text(min_size=1, max_size=100).filter(
    lambda x: x.strip() != '' and not any(c in x for c in ['\x00', '\n', '\r'])
)

# Strategy for valid names
name_strategy = st.text(min_size=1, max_size=100).filter(
    lambda x: x.strip() != '' and not any(c in x for c in ['\x00', '\n', '\r'])
)


@given(namespace=namespace_strategy)
def test_eksinfo_round_trip(namespace):
    """Property: EksInfo should preserve data through to_dict/from_dict round-trip"""
    # Create an EksInfo instance
    original = emr.EksInfo(Namespace=namespace)
    
    # Convert to dict
    dict_repr = original.to_dict()
    
    # Recreate from dict
    recreated = emr.EksInfo.from_dict('TestTitle', dict_repr)
    recreated_dict = recreated.to_dict()
    
    # Property: round-trip should preserve data
    assert dict_repr == recreated_dict, f"Round-trip failed: {dict_repr} != {recreated_dict}"


@given(
    namespace=namespace_strategy,
    provider_id=id_strategy,
    provider_type=st.sampled_from(['EKS', 'ECS', 'FARGATE'])
)
def test_container_provider_round_trip(namespace, provider_id, provider_type):
    """Property: ContainerProvider with nested objects should preserve structure"""
    # Create nested structure
    eks_info = emr.EksInfo(Namespace=namespace)
    container_info = emr.ContainerInfo(EksInfo=eks_info)
    provider = emr.ContainerProvider(
        Id=provider_id,
        Info=container_info,
        Type=provider_type
    )
    
    # Convert to dict
    dict_repr = provider.to_dict()
    
    # Recreate from dict
    recreated = emr.ContainerProvider.from_dict('TestTitle', dict_repr)
    recreated_dict = recreated.to_dict()
    
    # Property: nested structure should be preserved
    assert dict_repr == recreated_dict
    assert dict_repr['Info']['EksInfo']['Namespace'] == namespace


@given(
    namespace=namespace_strategy,
    cluster_name=name_strategy,
    provider_id=id_strategy,
    include_tags=st.booleans(),
    include_security=st.booleans()
)
def test_virtual_cluster_complete_structure(namespace, cluster_name, provider_id, 
                                           include_tags, include_security):
    """Property: VirtualCluster should maintain complete structure with optional fields"""
    # Create complete structure
    eks_info = emr.EksInfo(Namespace=namespace)
    container_info = emr.ContainerInfo(EksInfo=eks_info)
    provider = emr.ContainerProvider(
        Id=provider_id,
        Info=container_info,
        Type='EKS'
    )
    
    kwargs = {
        'title': 'TestCluster',
        'Name': cluster_name,
        'ContainerProvider': provider
    }
    
    if include_tags:
        kwargs['Tags'] = troposphere.Tags(Environment='test', Project='hypothesis')
    
    if include_security:
        kwargs['SecurityConfigurationId'] = 'sec-' + provider_id[:10]
    
    cluster = emr.VirtualCluster(**kwargs)
    
    # Convert to dict
    cluster_dict = cluster.to_dict()
    
    # Verify structure
    assert cluster_dict['Type'] == 'AWS::EMRContainers::VirtualCluster'
    assert cluster_dict['Properties']['Name'] == cluster_name
    assert cluster_dict['Properties']['ContainerProvider']['Id'] == provider_id
    
    if include_tags:
        tags = cluster_dict['Properties']['Tags']
        assert isinstance(tags, list)
        assert len(tags) == 2
        tag_dict = {tag['Key']: tag['Value'] for tag in tags}
        assert tag_dict['Environment'] == 'test'
        assert tag_dict['Project'] == 'hypothesis'
    
    if include_security:
        assert cluster_dict['Properties']['SecurityConfigurationId'] == 'sec-' + provider_id[:10]


@given(invalid_value=st.one_of(
    st.integers(),
    st.floats(),
    st.lists(st.text()),
    st.dictionaries(st.text(), st.text()),
    st.booleans(),
    st.none()
))
def test_type_validation_rejects_invalid_types(invalid_value):
    """Property: Type validation should reject non-string values for string fields"""
    # Test EksInfo Namespace field
    with pytest.raises((TypeError, ValueError)) as exc_info:
        eks = emr.EksInfo(Namespace=invalid_value)
        eks.to_dict()  # Validation happens here
    
    # Verify we get a meaningful error about type mismatch
    error_msg = str(exc_info.value)
    assert 'expected <class \'str\'>' in error_msg or 'must be' in error_msg


@given(st.data())
def test_required_fields_validation(data):
    """Property: Required fields must be present for successful validation"""
    # Test missing required field in ContainerProvider
    eks_info = emr.EksInfo(Namespace='test')
    container_info = emr.ContainerInfo(EksInfo=eks_info)
    
    # Choose which required field to omit
    omit_field = data.draw(st.sampled_from(['Id', 'Info', 'Type']))
    
    kwargs = {
        'Id': 'test-id',
        'Info': container_info,
        'Type': 'EKS'
    }
    
    # Remove one required field
    del kwargs[omit_field]
    
    # Should raise error when trying to validate
    with pytest.raises(ValueError) as exc_info:
        provider = emr.ContainerProvider(**kwargs)
        provider.to_dict()
    
    error_msg = str(exc_info.value)
    assert f'Resource {omit_field} required' in error_msg


@given(
    namespace1=namespace_strategy,
    namespace2=namespace_strategy
)
def test_eksinfo_equality_property(namespace1, namespace2):
    """Property: Two EksInfo instances with same namespace should produce identical dicts"""
    eks1 = emr.EksInfo(Namespace=namespace1)
    eks2 = emr.EksInfo(Namespace=namespace1)
    eks3 = emr.EksInfo(Namespace=namespace2)
    
    dict1 = eks1.to_dict()
    dict2 = eks2.to_dict()
    dict3 = eks3.to_dict()
    
    # Same namespace should produce same dict
    assert dict1 == dict2
    
    # Different namespace should produce different dict (unless they happen to be equal)
    if namespace1 != namespace2:
        assert dict1 != dict3


@given(st.text())
def test_namespace_handles_unicode_and_special_chars(text):
    """Property: EksInfo should handle any valid string including unicode"""
    # Skip truly empty strings as they might not be valid namespaces
    assume(text.strip() != '')
    
    try:
        eks = emr.EksInfo(Namespace=text)
        result = eks.to_dict()
        
        # The namespace should be preserved exactly
        assert result['Namespace'] == text
        
        # Round-trip should work
        recreated = emr.EksInfo.from_dict('Title', result)
        assert recreated.to_dict()['Namespace'] == text
    except (UnicodeDecodeError, UnicodeEncodeError):
        # Some extreme unicode might fail, that's OK
        pass


@given(
    title=st.text(min_size=1),
    namespace=namespace_strategy
)
def test_from_dict_with_various_titles(title, namespace):
    """Property: from_dict should work with any non-empty title"""
    eks = emr.EksInfo(Namespace=namespace)
    dict_repr = eks.to_dict()
    
    # Should work with any title
    recreated = emr.EksInfo.from_dict(title, dict_repr)
    
    # The data should be preserved regardless of title
    assert recreated.to_dict() == dict_repr


@given(st.data())
def test_virtualcluster_getatt_and_ref_methods(data):
    """Property: VirtualCluster GetAtt and Ref methods should return consistent values"""
    namespace = data.draw(namespace_strategy)
    cluster_name = data.draw(name_strategy)
    provider_id = data.draw(id_strategy)
    
    # Create a VirtualCluster
    cluster = emr.VirtualCluster(
        title='TestCluster',
        Name=cluster_name,
        ContainerProvider=emr.ContainerProvider(
            Id=provider_id,
            Info=emr.ContainerInfo(
                EksInfo=emr.EksInfo(Namespace=namespace)
            ),
            Type='EKS'
        )
    )
    
    # Test Ref method
    ref_result = cluster.Ref()
    assert ref_result == {'Ref': 'TestCluster'}
    
    # Test ref property (lowercase)
    ref_prop = cluster.ref()
    assert ref_prop == {'Ref': 'TestCluster'}
    
    # Both should be equal
    assert ref_result == ref_prop
    
    # Test GetAtt with various attributes
    valid_attrs = ['Arn', 'Id', 'Name']
    attr = data.draw(st.sampled_from(valid_attrs))
    
    getatt_result = cluster.GetAtt(attr)
    assert getatt_result == {'Fn::GetAtt': ['TestCluster', attr]}
    
    # Test get_att method (lowercase)
    get_att_result = cluster.get_att(attr)
    assert get_att_result == {'Fn::GetAtt': ['TestCluster', attr]}
    
    # Both should be equal
    assert getatt_result == get_att_result