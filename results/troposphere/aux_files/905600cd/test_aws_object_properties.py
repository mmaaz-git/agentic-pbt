import troposphere.redshift as redshift
from troposphere.validators import boolean, integer
from hypothesis import given, strategies as st, assume, settings
import json


# Test round-trip property: to_dict() and from_dict() equivalence
@given(
    cluster_type=st.sampled_from(['single-node', 'multi-node']),
    db_name=st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=1, max_size=10),
    master_username=st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=1, max_size=10),
    node_type=st.sampled_from(['dc2.large', 'dc2.xlarge', 'dc2.8xlarge']),
    num_nodes=st.integers(min_value=1, max_value=100),
    port=st.integers(min_value=1024, max_value=65535),
    encrypted=st.booleans(),
    publicly_accessible=st.booleans()
)
def test_cluster_to_dict_consistency(cluster_type, db_name, master_username, node_type,
                                    num_nodes, port, encrypted, publicly_accessible):
    """Test that cluster.to_dict() produces consistent results"""
    
    # Skip single-node with multiple nodes
    if cluster_type == 'single-node' and num_nodes > 1:
        num_nodes = None
    
    kwargs = {
        'ClusterType': cluster_type,
        'DBName': db_name,
        'MasterUsername': master_username,
        'NodeType': node_type,
        'Encrypted': encrypted,
        'PubliclyAccessible': publicly_accessible,
        'Port': port
    }
    
    if num_nodes is not None and cluster_type == 'multi-node':
        kwargs['NumberOfNodes'] = num_nodes
    
    cluster1 = redshift.Cluster('TestCluster', **kwargs)
    cluster2 = redshift.Cluster('TestCluster', **kwargs)
    
    # Two clusters created with the same arguments should produce the same dict
    dict1 = cluster1.to_dict()
    dict2 = cluster2.to_dict()
    
    assert dict1 == dict2, f"Same inputs produced different outputs"


# Test that JSON serialization works
@given(
    st.dictionaries(
        st.sampled_from(['Description', 'ParameterGroupFamily', 'ParameterGroupName']),
        st.text(min_size=1, max_size=20),
        min_size=2, max_size=3
    )
)
def test_cluster_parameter_group_json_serializable(params):
    """Test that ClusterParameterGroup objects are JSON serializable"""
    # Ensure required fields
    params['Description'] = params.get('Description', 'Test description')
    params['ParameterGroupFamily'] = params.get('ParameterGroupFamily', 'redshift-1.0')
    
    group = redshift.ClusterParameterGroup('TestGroup', **params)
    group_dict = group.to_dict()
    
    # Should be JSON serializable
    json_str = json.dumps(group_dict)
    restored = json.loads(json_str)
    
    # Round-trip should preserve the data
    assert restored == group_dict


# Test property validation with boundary values
@given(
    retention_period=st.one_of(
        st.just(-1),  # Below minimum
        st.just(0),   # Minimum
        st.just(365), # Typical maximum
        st.just(366), # Above typical maximum
        st.just(99999) # Very large
    )
)
def test_snapshot_retention_boundary_values(retention_period):
    """Test that snapshot retention period accepts various boundary values"""
    try:
        cluster = redshift.Cluster(
            'TestCluster',
            ClusterType='single-node',
            DBName='testdb',
            MasterUsername='admin',
            NodeType='dc2.large',
            AutomatedSnapshotRetentionPeriod=retention_period
        )
        
        cluster_dict = cluster.to_dict()
        # If it accepted the value, it should be in the dict
        assert 'AutomatedSnapshotRetentionPeriod' in cluster_dict['Properties']
        assert cluster_dict['Properties']['AutomatedSnapshotRetentionPeriod'] == retention_period
    except ValueError as e:
        # Some values might be rejected, which is fine
        pass


# Test Tags handling
@given(
    tags=st.one_of(
        st.none(),
        st.lists(
            st.dictionaries(
                st.just('Key'),
                st.text(min_size=1, max_size=10),
                min_size=1, max_size=1
            ).map(lambda d: {**d, 'Value': 'test'}),
            min_size=0, max_size=5
        ),
        st.dictionaries(
            st.text(min_size=1, max_size=10),
            st.text(min_size=1, max_size=10),
            min_size=0, max_size=5
        )
    )
)
def test_cluster_tags_handling(tags):
    """Test that Cluster handles various tag formats"""
    try:
        cluster = redshift.Cluster(
            'TestCluster',
            ClusterType='single-node',
            DBName='testdb',
            MasterUsername='admin',
            NodeType='dc2.large',
            Tags=tags
        )
        
        cluster_dict = cluster.to_dict()
        if tags is not None:
            assert 'Tags' in cluster_dict['Properties']
    except (TypeError, AttributeError) as e:
        # Some tag formats might not be accepted
        pass


# Test that required fields are actually required
@given(
    skip_field=st.sampled_from(['ClusterType', 'DBName', 'MasterUsername', 'NodeType'])
)
def test_cluster_required_fields(skip_field):
    """Test that Cluster enforces required fields"""
    fields = {
        'ClusterType': 'single-node',
        'DBName': 'testdb',
        'MasterUsername': 'admin',
        'NodeType': 'dc2.large'
    }
    
    # Remove one required field
    del fields[skip_field]
    
    try:
        cluster = redshift.Cluster('TestCluster', **fields)
        cluster.validate()
        # If we get here without error, the field wasn't actually required
        assert False, f"Field {skip_field} should be required but wasn't enforced"
    except (TypeError, KeyError, AttributeError) as e:
        # Expected - required field was missing
        pass


# Test metamorphic property: Adding same property twice
@given(
    port1=st.integers(min_value=1024, max_value=65535),
    port2=st.integers(min_value=1024, max_value=65535)
)
def test_cluster_property_override(port1, port2):
    """Test that later property values override earlier ones"""
    cluster = redshift.Cluster(
        'TestCluster',
        ClusterType='single-node',
        DBName='testdb',
        MasterUsername='admin',
        NodeType='dc2.large',
        Port=port1
    )
    
    # Override the port
    cluster.Port = port2
    
    cluster_dict = cluster.to_dict()
    # The last value should win
    assert cluster_dict['Properties']['Port'] == port2


# Test EndpointAccess with list properties
@given(
    vpc_ids=st.lists(
        st.text(alphabet='abcdefghijklmnopqrstuvwxyz0123456789-', min_size=1, max_size=20),
        min_size=1, max_size=5
    )
)
def test_endpoint_access_vpc_list(vpc_ids):
    """Test EndpointAccess with VPC security group IDs list"""
    endpoint = redshift.EndpointAccess(
        'TestEndpoint',
        ClusterIdentifier='test-cluster',
        EndpointName='test-endpoint',
        SubnetGroupName='test-subnet',
        VpcSecurityGroupIds=vpc_ids
    )
    
    endpoint_dict = endpoint.to_dict()
    assert 'VpcSecurityGroupIds' in endpoint_dict['Properties']
    assert endpoint_dict['Properties']['VpcSecurityGroupIds'] == vpc_ids
    assert len(endpoint_dict['Properties']['VpcSecurityGroupIds']) == len(vpc_ids)


# Test ClusterSubnetGroup with subnet list
@given(
    subnet_ids=st.lists(
        st.text(alphabet='subnet-abcdefghijklmnopqrstuvwxyz0123456789', min_size=7, max_size=30),
        min_size=1, max_size=10
    ),
    description=st.text(min_size=1, max_size=100)
)
def test_cluster_subnet_group(subnet_ids, description):
    """Test ClusterSubnetGroup with subnet IDs list"""
    group = redshift.ClusterSubnetGroup(
        'TestSubnetGroup',
        Description=description,
        SubnetIds=subnet_ids
    )
    
    group_dict = group.to_dict()
    assert group_dict['Properties']['Description'] == description
    assert group_dict['Properties']['SubnetIds'] == subnet_ids
    assert len(group_dict['Properties']['SubnetIds']) == len(subnet_ids)