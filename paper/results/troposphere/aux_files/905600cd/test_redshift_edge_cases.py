import troposphere.redshift as redshift
from troposphere.validators import boolean, integer
from hypothesis import given, strategies as st, assume, settings
import math


# Test for edge cases with boolean validator
@given(st.one_of(
    st.text(),
    st.integers(),
    st.floats(allow_nan=True, allow_infinity=True),
    st.none(),
    st.lists(st.integers()),
    st.dictionaries(st.text(), st.text())
))
def test_boolean_invalid_inputs_raise_error(value):
    """Test that boolean() raises ValueError for invalid inputs"""
    # Skip the valid inputs
    if value in [True, 1, "1", "true", "True", False, 0, "0", "false", "False"]:
        assume(False)
    
    try:
        result = boolean(value)
        # If we get here, it means the validator accepted an unexpected value
        assert value in [True, 1, "1", "true", "True", False, 0, "0", "false", "False"], \
            f"boolean() accepted unexpected value: {value!r} -> {result!r}"
    except ValueError:
        # This is expected for invalid inputs
        pass
    except Exception as e:
        # Any other exception is unexpected
        assert False, f"Unexpected exception for {value!r}: {type(e).__name__}: {e}"


# Test case sensitivity edge cases
@given(st.text())
def test_boolean_case_sensitivity(text):
    """Test boolean validator's case sensitivity handling"""
    # The validator should only accept exact case matches for string booleans
    valid_strings = ["true", "True", "false", "False", "1", "0"]
    
    if text not in valid_strings:
        try:
            boolean(text)
            # If no exception, it means an invalid string was accepted
            assert False, f"boolean() should have rejected {text!r}"
        except ValueError:
            pass  # Expected


# Test integer validator with extreme values
@given(st.one_of(
    st.integers(min_value=-10**100, max_value=10**100),
    st.text(alphabet="0123456789-", min_size=1).filter(
        lambda x: x not in ['-', '--'] and not x.endswith('-') and x.count('-') <= 1
    )
))
def test_integer_extreme_values(value):
    """Test integer validator with very large numbers"""
    try:
        result = integer(value)
        # Should preserve the original value
        assert result == value
        # Should be convertible to int
        int(result)
    except ValueError:
        # If the string isn't a valid integer, this is expected
        if isinstance(value, str):
            try:
                int(value)
                # If int() works but integer() failed, that's a bug
                assert False, f"integer() rejected valid integer string: {value!r}"
            except ValueError:
                pass  # Both failed, which is consistent


# Test for potential hash/equality issues in AWS objects
@given(
    st.tuples(
        st.sampled_from([True, False, 1, 0, "true", "false"]),
        st.sampled_from([True, False, 1, 0, "true", "false"])
    )
)
def test_cluster_equality_with_normalized_booleans(bool_pair):
    """Test if clusters with equivalent boolean values are equal"""
    val1, val2 = bool_pair
    
    # Only test when the boolean values are equivalent
    if boolean(val1) != boolean(val2):
        assume(False)
    
    cluster1 = redshift.Cluster(
        'TestCluster',
        ClusterType='single-node',
        DBName='testdb',
        MasterUsername='admin',
        NodeType='dc2.large',
        Encrypted=val1
    )
    
    cluster2 = redshift.Cluster(
        'TestCluster',
        ClusterType='single-node',
        DBName='testdb',
        MasterUsername='admin',
        NodeType='dc2.large',
        Encrypted=val2
    )
    
    # After normalization, these should produce the same output
    dict1 = cluster1.to_dict()
    dict2 = cluster2.to_dict()
    
    # The Properties should be equal since booleans are normalized
    assert dict1['Properties']['Encrypted'] == dict2['Properties']['Encrypted']


# Test with mixed types in parameter lists
@given(st.lists(
    st.one_of(
        st.text(min_size=1),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False)
    ),
    min_size=2, max_size=2
))
def test_parameter_mixed_types(values):
    """Test AmazonRedshiftParameter with various value types"""
    try:
        param = redshift.AmazonRedshiftParameter(
            ParameterName=str(values[0]),
            ParameterValue=str(values[1])
        )
        
        # Should successfully create the parameter
        param_dict = param.to_dict()
        assert param_dict['ParameterName'] == str(values[0])
        assert param_dict['ParameterValue'] == str(values[1])
    except Exception as e:
        # Check if this is an expected error
        assert False, f"Unexpected error creating parameter: {e}"


# Test integer validator doesn't mutate input
@given(st.integers())
def test_integer_validator_immutability(value):
    """Test that integer validator doesn't mutate the input"""
    original = value
    result = integer(value)
    
    # The original value should be unchanged
    assert value == original
    # The result should equal the original
    assert result == original
    # They should be the same object for integers (due to Python's integer caching)
    if -5 <= value <= 256:  # Python caches small integers
        assert result is original


# Test Cluster with all boolean fields set
@given(st.dictionaries(
    st.sampled_from(['AllowVersionUpgrade', 'AvailabilityZoneRelocation', 'Classic',
                     'DeferMaintenance', 'Encrypted', 'EnhancedVpcRouting',
                     'ManageMasterPassword', 'MultiAZ', 'PubliclyAccessible',
                     'RotateEncryptionKey', 'SnapshotCopyManual']),
    st.sampled_from([True, False, 1, 0, "1", "0", "true", "false", "True", "False"]),
    min_size=1
))
def test_cluster_all_boolean_fields(bool_fields):
    """Test Cluster with multiple boolean fields set simultaneously"""
    cluster_args = {
        'ClusterType': 'single-node',
        'DBName': 'testdb',
        'MasterUsername': 'admin',
        'NodeType': 'dc2.large',
        **bool_fields
    }
    
    cluster = redshift.Cluster('TestCluster', **cluster_args)
    cluster_dict = cluster.to_dict()
    
    # All boolean fields should be properly normalized
    for field_name, field_value in bool_fields.items():
        assert field_name in cluster_dict['Properties']
        assert cluster_dict['Properties'][field_name] == boolean(field_value)
        assert isinstance(cluster_dict['Properties'][field_name], bool)


# Test for special string values that might break integer validator
@given(st.sampled_from([
    "0x10", "0o10", "0b10",  # Different bases
    "+123", " 123 ", "\t123\n",  # Whitespace and plus sign
    "1e2", "1.0", "1.5",  # Scientific notation and floats
    "∞", "NaN", "null", "undefined",  # Special values
    "", " ", "\n",  # Empty/whitespace
]))
def test_integer_special_strings(value):
    """Test integer validator with special string formats"""
    try:
        result = integer(value)
        # If it succeeds, verify it's actually valid
        int_val = int(result)
        # The result should be the same as input
        assert result == value
    except ValueError:
        # Make sure int() would also fail
        try:
            int(value)
            # If int() works but integer() failed, might be a bug
            # But integer() is allowed to be more restrictive
        except (ValueError, TypeError):
            pass  # Both failed, which is consistent