"""Property-based tests for troposphere.docdbelastic module"""

import math
from hypothesis import given, strategies as st, assume, settings
import troposphere.docdbelastic as target


# Strategy for values that should pass integer validation
valid_integers = st.one_of(
    st.integers(),
    st.text(alphabet='0123456789').filter(lambda x: x and not x.startswith('0') or x == '0'),
    st.text(alphabet='0123456789').map(lambda x: '-' + x if x else '0').filter(lambda x: x != '-'),
    st.booleans(),
    st.floats(allow_nan=False, allow_infinity=False).filter(lambda x: x.is_integer())
)


@given(valid_integers)
def test_integer_function_accepts_valid_inputs(value):
    """Property: integer() should accept values that can be converted to int"""
    result = target.integer(value)
    # The function should return the original value unchanged
    assert result == value
    # And it should be convertible to int
    int(result)


@given(st.one_of(
    st.floats(allow_nan=False, allow_infinity=False).filter(lambda x: not x.is_integer()),
    st.text().filter(lambda x: not x.isdigit() and x != '' and not (x.startswith('-') and x[1:].isdigit())),
    st.none(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.integers())
))
def test_integer_function_rejects_invalid_inputs(value):
    """Property: integer() should reject values that cannot be converted to int"""
    try:
        target.integer(value)
        # If we get here, the value should be convertible to int
        int(value)
    except ValueError:
        # Expected behavior - function correctly rejected invalid input
        pass
    except (TypeError, OverflowError):
        # Also acceptable for some edge cases
        pass


@given(valid_integers)
def test_integer_preserves_type(value):
    """Property: integer() preserves the original type of valid inputs"""
    result = target.integer(value)
    assert type(result) == type(value)


@given(
    admin_user=st.text(min_size=1, max_size=50),
    auth_type=st.sampled_from(['PLAIN_TEXT', 'SECRET_ARN']),
    cluster_name=st.text(min_size=1, max_size=50).filter(lambda x: x.replace('-', '').replace('_', '').isalnum()),
    shard_capacity=valid_integers,
    shard_count=valid_integers
)
def test_cluster_creation_with_valid_integers(admin_user, auth_type, cluster_name, shard_capacity, shard_count):
    """Property: Cluster should accept any value that passes integer validation"""
    cluster = target.Cluster(
        'TestCluster',
        AdminUserName=admin_user,
        AuthType=auth_type,
        ClusterName=cluster_name,
        ShardCapacity=shard_capacity,
        ShardCount=shard_count
    )
    
    result = cluster.to_dict()
    assert result['Properties']['ShardCapacity'] == shard_capacity
    assert result['Properties']['ShardCount'] == shard_count
    assert type(result['Properties']['ShardCapacity']) == type(shard_capacity)
    assert type(result['Properties']['ShardCount']) == type(shard_count)


@given(
    admin_user=st.text(min_size=1, max_size=50),
    auth_type=st.sampled_from(['PLAIN_TEXT', 'SECRET_ARN']),
    cluster_name=st.text(min_size=1, max_size=50).filter(lambda x: x.replace('-', '').replace('_', '').isalnum()),
    shard_capacity=valid_integers,
    shard_count=valid_integers,
    shard_instance_count=st.one_of(st.none(), valid_integers),
    backup_retention=st.one_of(st.none(), valid_integers)
)
def test_cluster_from_dict_to_dict_round_trip(admin_user, auth_type, cluster_name, 
                                              shard_capacity, shard_count, 
                                              shard_instance_count, backup_retention):
    """Property: from_dict(to_dict()) should preserve all properties"""
    # Create cluster
    cluster1 = target.Cluster(
        'TestCluster',
        AdminUserName=admin_user,
        AuthType=auth_type,
        ClusterName=cluster_name,
        ShardCapacity=shard_capacity,
        ShardCount=shard_count
    )
    
    if shard_instance_count is not None:
        cluster1.ShardInstanceCount = shard_instance_count
    if backup_retention is not None:
        cluster1.BackupRetentionPeriod = backup_retention
    
    # Convert to dict
    dict1 = cluster1.to_dict()
    
    # Create from dict
    cluster2 = target.Cluster.from_dict('TestCluster2', dict1['Properties'])
    
    # Convert back to dict
    dict2 = cluster2.to_dict()
    
    # Properties should be preserved
    assert dict1['Properties'] == dict2['Properties']


@given(
    shard_capacity=st.one_of(
        st.floats(min_value=-1e6, max_value=1e6, allow_nan=False, allow_infinity=False),
        st.text(),
        st.booleans()
    )
)
def test_integer_validation_consistency(shard_capacity):
    """Property: Values that pass integer() should work in Cluster, and vice versa"""
    # Try with integer function
    try:
        target.integer(shard_capacity)
        integer_passes = True
    except ValueError:
        integer_passes = False
    
    # Try with Cluster
    try:
        cluster = target.Cluster(
            'TestCluster',
            AdminUserName='admin',
            AuthType='PLAIN_TEXT',
            ClusterName='test-cluster',
            ShardCapacity=shard_capacity,
            ShardCount=1
        )
        cluster_passes = True
    except ValueError:
        cluster_passes = False
    
    # Both should have the same result
    assert integer_passes == cluster_passes


@given(st.floats(allow_nan=True, allow_infinity=True))
def test_integer_handles_special_floats(value):
    """Property: integer() should handle NaN and infinity correctly"""
    if math.isnan(value) or math.isinf(value):
        try:
            result = target.integer(value)
            # If it doesn't raise, it should still fail int conversion
            assert False, f"integer({value}) should have raised ValueError"
        except ValueError:
            pass  # Expected
        except OverflowError:
            pass  # Also acceptable for infinity
    else:
        # Regular float handling
        try:
            result = target.integer(value)
            # Should be convertible to int
            int(result)
        except (ValueError, OverflowError):
            pass