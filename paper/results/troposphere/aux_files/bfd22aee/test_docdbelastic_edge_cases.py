"""Edge case tests for troposphere.docdbelastic module"""

import sys
from hypothesis import given, strategies as st, assume, settings, example
import troposphere.docdbelastic as target


@given(st.integers(min_value=-sys.maxsize, max_value=sys.maxsize))
def test_integer_with_extreme_values(value):
    """Test integer function with extreme integer values"""
    result = target.integer(value)
    assert result == value
    assert int(result) == value


@given(st.text(alphabet='0123456789', min_size=50, max_size=1000))
def test_integer_with_huge_numeric_strings(value):
    """Test integer function with very large numeric strings"""
    # These should all be valid
    result = target.integer(value)
    assert result == value
    # Should be convertible to int even if huge
    int(result)


@given(st.text(alphabet='0123456789+-', min_size=1, max_size=100))
def test_integer_with_malformed_numeric_strings(value):
    """Test integer function with potentially malformed numeric strings"""
    try:
        result = target.integer(value)
        # If it passes, it should be convertible to int
        int(result)
    except ValueError:
        # Should fail for malformed strings
        try:
            int(value)
            # If int() works, then integer() should have worked too
            assert False, f"integer() rejected {value} but int() accepts it"
        except ValueError:
            # Both correctly reject it
            pass


@given(st.floats(min_value=0.0, max_value=1.0, exclude_min=True, exclude_max=True))
def test_integer_with_small_floats(value):
    """Test integer function with floats between 0 and 1"""
    # These should all fail since they're not integers
    try:
        result = target.integer(value)
        assert False, f"integer() should reject {value}"
    except ValueError:
        pass


@given(st.floats())
@example(float('inf'))
@example(float('-inf'))
@example(float('nan'))
def test_integer_special_float_values(value):
    """Test integer function with special float values"""
    import math
    if math.isnan(value) or math.isinf(value):
        try:
            result = target.integer(value)
            # Should not accept NaN or infinity
            assert False, f"integer() should reject {value}"
        except (ValueError, OverflowError):
            pass
    else:
        # Regular float handling
        if value.is_integer():
            result = target.integer(value)
            assert result == value
        else:
            try:
                result = target.integer(value)
                assert False, f"integer() should reject non-integer float {value}"
            except ValueError:
                pass


class CustomInt:
    """Custom class that implements __int__"""
    def __init__(self, value):
        self.value = value
    
    def __int__(self):
        return self.value


def test_integer_with_custom_int_class():
    """Test integer function with custom class implementing __int__"""
    custom = CustomInt(42)
    result = target.integer(custom)
    assert result is custom
    assert int(result) == 42


class BadInt:
    """Custom class with broken __int__"""
    def __int__(self):
        raise RuntimeError("Broken __int__")


def test_integer_with_broken_int_class():
    """Test integer function with class that has broken __int__"""
    bad = BadInt()
    try:
        result = target.integer(bad)
        assert False, "Should have failed with broken __int__"
    except (ValueError, RuntimeError):
        pass


@given(st.sampled_from(['', ' ', '  ', '\t', '\n', ' 42 ', '42 ', ' 42']))
def test_integer_with_whitespace(value):
    """Test integer function with strings containing whitespace"""
    try:
        result = target.integer(value)
        # If it passes, int() should also work
        int(result)
    except ValueError:
        # Check if int() would also fail
        try:
            int(value)
            # If int() works but integer() doesn't, that's inconsistent
            assert False, f"integer() rejected '{value}' but int() accepts it"
        except ValueError:
            pass


@given(st.sampled_from(['+42', '-42', '++42', '--42', '+-42', '-+42']))
def test_integer_with_sign_prefixes(value):
    """Test integer function with various sign prefixes"""
    try:
        result = target.integer(value)
        # If it passes, int() should also work
        converted = int(result)
        # And conversion should match direct int()
        assert converted == int(value)
    except ValueError:
        # Check if int() would also fail
        try:
            int(value)
            # If int() works but integer() doesn't, that's inconsistent
            assert False, f"integer() rejected '{value}' but int() accepts it"
        except ValueError:
            pass


@given(st.sampled_from(['0x42', '0o42', '0b101', '0X42', '0O42', '0B101']))
def test_integer_with_base_prefixes(value):
    """Test integer function with different base representations"""
    try:
        result = target.integer(value)
        # If it passes, int() with base 0 should work
        converted = int(result, 0)
    except ValueError:
        # These should typically fail since integer() doesn't handle bases
        pass
    except TypeError:
        # This is also fine - means integer() returned non-string
        pass


@given(st.dictionaries(
    st.sampled_from(['ShardCapacity', 'ShardCount', 'BackupRetentionPeriod', 'ShardInstanceCount']),
    st.one_of(
        st.just(sys.maxsize),
        st.just(-sys.maxsize),
        st.just(0),
        st.floats(min_value=1e100, max_value=1e200),
        st.text(alphabet='0123456789', min_size=100, max_size=200)
    ),
    min_size=1
))
def test_cluster_with_extreme_integer_properties(props):
    """Test Cluster with extreme values for integer properties"""
    base_props = {
        'AdminUserName': 'admin',
        'AuthType': 'PLAIN_TEXT',
        'ClusterName': 'test',
        'ShardCapacity': 1,
        'ShardCount': 1
    }
    base_props.update(props)
    
    try:
        cluster = target.Cluster.from_dict('Test', base_props)
        result = cluster.to_dict()
        # Verify values are preserved
        for key, value in props.items():
            assert result['Properties'][key] == value
    except (ValueError, OverflowError) as e:
        # Check if the error is from integer validation
        for value in props.values():
            try:
                target.integer(value)
            except (ValueError, OverflowError):
                # Expected - value doesn't pass integer validation
                break
        else:
            # All values passed integer() but Cluster failed?
            raise AssertionError(f"Cluster rejected values that pass integer(): {props}") from e