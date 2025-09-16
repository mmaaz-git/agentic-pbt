"""Property-based tests for troposphere.securitylake module"""

import math
from hypothesis import given, strategies as st, assume
import troposphere.securitylake as sl


# Test 1: integer function validation inconsistency
@given(st.floats())
def test_integer_function_float_handling(x):
    """Test that integer function handles floats consistently"""
    # The function accepts floats but fails on inf/nan
    # This tests if the validation is consistent
    if math.isnan(x) or math.isinf(x):
        # Should raise an error for inf/nan
        try:
            result = sl.integer(x)
            # If we get here, it didn't raise - that's a bug
            assert False, f"integer({x}) should raise but returned {result}"
        except (ValueError, OverflowError):
            pass  # Expected
    else:
        # Should either accept or reject consistently
        try:
            result = sl.integer(x)
            # If accepted, should preserve the value
            assert result == x, f"integer({x}) returned {result}"
        except ValueError:
            # Should only reject if not a valid number
            assert False, f"integer({x}) raised ValueError but {x} is a valid float"


# Test 2: Boolean handling inconsistency
@given(st.booleans())
def test_integer_function_boolean_handling(b):
    """Test that integer function handles booleans as integers"""
    # The function accepts booleans - but are they treated as 0/1?
    result = sl.integer(b)
    assert result == b  # Returns the boolean unchanged
    # This is potentially problematic as booleans are integers in Python
    # but the function doesn't convert them


# Test 3: String integer validation
@given(st.text())
def test_integer_function_string_validation(s):
    """Test string validation in integer function"""
    try:
        result = sl.integer(s)
        # If it accepts a string, it should be a valid integer string
        # Let's check if it's actually validating properly
        if s.strip() != s:
            # Strings with whitespace are accepted without stripping
            assert result == s  # Returns unchanged
        else:
            # Should be a valid integer string
            try:
                int(s)
            except ValueError:
                # s is not a valid integer but integer() accepted it
                assert False, f"integer() accepted non-integer string: {s!r}"
    except ValueError:
        # Should reject non-integer strings
        pass


# Test 4: Type validation property
@given(st.integers())
def test_aws_object_type_validation(val):
    """Test that AWS objects properly validate property types"""
    # MetaStoreManagerRoleArn expects a string
    try:
        lake = sl.DataLake('Test', MetaStoreManagerRoleArn=val)
        # Should have rejected non-string
        assert False, f"DataLake accepted integer {val} for string property"
    except TypeError:
        pass  # Expected


# Test 5: Property mutation after creation
@given(st.text(), st.text())
def test_property_mutation(arn1, arn2):
    """Test that properties can be mutated after object creation"""
    assume(arn1 != arn2)  # Only test with different values
    
    source = sl.AwsLogSource(
        'Test',
        DataLakeArn=arn1,
        SourceName='test',
        SourceVersion='1.0'
    )
    
    # Get initial value
    dict1 = source.to_dict()
    assert dict1['Properties']['DataLakeArn'] == arn1
    
    # Mutate the property
    source.DataLakeArn = arn2
    
    # Check it changed
    dict2 = source.to_dict()
    assert dict2['Properties']['DataLakeArn'] == arn2
    assert dict2['Properties']['DataLakeArn'] != arn1


# Test 6: List property handling
@given(st.lists(st.text()))
def test_accounts_list_property(accounts):
    """Test that Accounts property handles lists correctly"""
    source = sl.AwsLogSource(
        'Test',
        DataLakeArn='test-arn',
        SourceName='test',
        SourceVersion='1.0',
        Accounts=accounts
    )
    
    result = source.to_dict()
    # Should preserve the list exactly
    assert result['Properties']['Accounts'] == accounts
    
    # Check if duplicates are preserved
    if len(accounts) != len(set(accounts)):
        # Has duplicates
        assert result['Properties']['Accounts'] == accounts  # Should preserve duplicates


# Test 7: Empty string handling
@given(st.sampled_from(['', ' ', '  ', '\t', '\n']))
def test_empty_or_whitespace_strings(s):
    """Test handling of empty and whitespace strings in required fields"""
    # DataLakeArn is required - but does it validate emptiness?
    source = sl.AwsLogSource(
        'Test',
        DataLakeArn=s,
        SourceName='test',
        SourceVersion='1.0'
    )
    
    result = source.to_dict()
    # Empty strings are accepted even for required fields
    assert result['Properties']['DataLakeArn'] == s
    # This could be a bug - required fields accepting empty strings


# Test 8: integer function with numeric strings
@given(st.integers(min_value=-10**18, max_value=10**18))
def test_integer_function_numeric_string_round_trip(n):
    """Test that integer function preserves numeric strings"""
    s = str(n)
    result = sl.integer(s)
    # It returns the string unchanged, not converting to int
    assert result == s
    assert type(result) == str
    # This means Days='30' stays as string '30', not int 30