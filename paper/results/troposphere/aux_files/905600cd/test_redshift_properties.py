import troposphere.redshift as redshift
from troposphere.validators import boolean, integer
from hypothesis import given, strategies as st, assume
import math


# Test 1: Boolean validator idempotence property
@given(st.sampled_from([True, 1, "1", "true", "True", False, 0, "0", "false", "False"]))
def test_boolean_idempotence(value):
    """Test that boolean(boolean(x)) == boolean(x) for all valid inputs"""
    result1 = boolean(value)
    result2 = boolean(result1)
    assert result1 == result2


# Test 2: Boolean validator preserves actual booleans
@given(st.booleans())
def test_boolean_preserves_booleans(value):
    """Test that boolean(True) == True and boolean(False) == False"""
    assert boolean(value) == value


# Test 3: Integer validator preserves valid inputs
@given(st.one_of(
    st.integers(),
    st.text().filter(lambda x: x.strip() and x.strip().lstrip('-').isdigit()),
))
def test_integer_preserves_input(value):
    """Test that integer(x) returns x unchanged when x is valid"""
    result = integer(value)
    assert result == value


# Test 4: Integer validator accepts string representations
@given(st.integers(min_value=-10**10, max_value=10**10))
def test_integer_accepts_string_representations(num):
    """Test that integer() accepts string representations of integers"""
    str_num = str(num)
    result = integer(str_num)
    assert result == str_num
    # Verify it's actually a valid integer string
    assert int(result) == num


# Test 5: Test AWS Cluster object with various boolean representations  
@given(
    allow_upgrade=st.sampled_from([True, False, 1, 0, "true", "false", "1", "0"]),
    encrypted=st.sampled_from([True, False, 1, 0, "true", "false", "1", "0"]),
    publicly_accessible=st.sampled_from([True, False, 1, 0, "true", "false", "1", "0"])
)
def test_cluster_boolean_normalization(allow_upgrade, encrypted, publicly_accessible):
    """Test that Cluster normalizes various boolean representations correctly"""
    cluster = redshift.Cluster(
        'TestCluster',
        ClusterType='single-node',
        DBName='testdb',
        MasterUsername='admin',
        NodeType='dc2.large',
        AllowVersionUpgrade=allow_upgrade,
        Encrypted=encrypted,
        PubliclyAccessible=publicly_accessible
    )
    
    cluster_dict = cluster.to_dict()
    props = cluster_dict['Properties']
    
    # Check that booleans are properly normalized
    assert props['AllowVersionUpgrade'] == boolean(allow_upgrade)
    assert props['Encrypted'] == boolean(encrypted)
    assert props['PubliclyAccessible'] == boolean(publicly_accessible)
    
    # All should be actual booleans
    assert isinstance(props['AllowVersionUpgrade'], bool)
    assert isinstance(props['Encrypted'], bool)
    assert isinstance(props['PubliclyAccessible'], bool)


# Test 6: Test Cluster with integer string representations
@given(
    num_nodes=st.integers(min_value=1, max_value=100),
    port=st.integers(min_value=1024, max_value=65535),
    retention_period=st.integers(min_value=0, max_value=365)
)
def test_cluster_integer_string_handling(num_nodes, port, retention_period):
    """Test that Cluster accepts both integer and string representations of integers"""
    # Test with string representations
    cluster1 = redshift.Cluster(
        'TestCluster1',
        ClusterType='multi-node',
        DBName='testdb',
        MasterUsername='admin',
        NodeType='dc2.large',
        NumberOfNodes=str(num_nodes),
        Port=str(port),
        AutomatedSnapshotRetentionPeriod=str(retention_period)
    )
    
    # Test with actual integers
    cluster2 = redshift.Cluster(
        'TestCluster2',
        ClusterType='multi-node',
        DBName='testdb',
        MasterUsername='admin',
        NodeType='dc2.large',
        NumberOfNodes=num_nodes,
        Port=port,
        AutomatedSnapshotRetentionPeriod=retention_period
    )
    
    dict1 = cluster1.to_dict()['Properties']
    dict2 = cluster2.to_dict()['Properties']
    
    # Both should work and preserve the original type
    assert dict1['NumberOfNodes'] == str(num_nodes)
    assert dict2['NumberOfNodes'] == num_nodes
    
    # The integer validator should preserve the input type
    assert integer(str(num_nodes)) == str(num_nodes)
    assert integer(num_nodes) == num_nodes


# Test 7: Test for edge case with integer validator - preserves type
@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False).filter(lambda x: x == int(x))
))
def test_integer_validator_type_preservation(value):
    """Test that integer validator preserves the exact input (not converting it)"""
    if isinstance(value, float):
        # Convert float to int for this test since we're testing integers
        value = int(value)
    
    result = integer(value)
    assert result == value
    assert type(result) == type(value)


# Test 8: Multiple boolean fields interaction
@given(st.lists(
    st.sampled_from([True, False, 1, 0, "true", "false", "1", "0"]),
    min_size=3, max_size=3
))
def test_multiple_boolean_fields(bool_values):
    """Test that multiple boolean fields don't interfere with each other"""
    cluster = redshift.Cluster(
        'TestCluster',
        ClusterType='single-node',
        DBName='testdb',
        MasterUsername='admin',
        NodeType='dc2.large',
        AllowVersionUpgrade=bool_values[0],
        Encrypted=bool_values[1],
        PubliclyAccessible=bool_values[2]
    )
    
    props = cluster.to_dict()['Properties']
    
    # Each should be independently normalized
    assert props['AllowVersionUpgrade'] == boolean(bool_values[0])
    assert props['Encrypted'] == boolean(bool_values[1])
    assert props['PubliclyAccessible'] == boolean(bool_values[2])


# Test 9: Test ClusterParameterGroup with list of parameters
@given(st.lists(
    st.tuples(
        st.text(min_size=1, max_size=50).filter(lambda x: not x.isspace()),
        st.text(min_size=1, max_size=50).filter(lambda x: not x.isspace())
    ),
    min_size=0, max_size=5
))
def test_cluster_parameter_group_parameters(param_pairs):
    """Test that ClusterParameterGroup correctly handles parameter lists"""
    parameters = [
        redshift.AmazonRedshiftParameter(
            ParameterName=name,
            ParameterValue=value
        )
        for name, value in param_pairs
    ]
    
    group = redshift.ClusterParameterGroup(
        'TestParamGroup',
        Description='Test parameter group',
        ParameterGroupFamily='redshift-1.0',
        Parameters=parameters
    )
    
    group_dict = group.to_dict()
    assert 'Properties' in group_dict
    if parameters:
        assert 'Parameters' in group_dict['Properties']
        assert len(group_dict['Properties']['Parameters']) == len(parameters)
        
        for i, (name, value) in enumerate(param_pairs):
            param = group_dict['Properties']['Parameters'][i]
            assert param['ParameterName'] == name
            assert param['ParameterValue'] == value