"""More aggressive property-based tests to find bugs in troposphere.securitylake"""

import math
from hypothesis import given, strategies as st, assume, settings
import troposphere.securitylake as sl
import json


# Test for potential bug with special float values
@given(st.floats(allow_nan=False, allow_infinity=False))
def test_expiration_days_float_preservation(days):
    """Test that Expiration Days handles floats correctly"""
    exp = sl.Expiration(Days=days)
    result = exp.to_dict()
    
    # The Days value should be preserved exactly
    assert result['Days'] == days
    
    # But what happens when we serialize to JSON?
    try:
        json_str = json.dumps(result)
        parsed = json.loads(json_str)
        # Check if round-trip preserves the value
        if not math.isclose(parsed['Days'], days, rel_tol=1e-9, abs_tol=1e-9):
            assert False, f"JSON round-trip changed {days} to {parsed['Days']}"
    except (TypeError, ValueError) as e:
        # JSON serialization might fail for some floats
        pass


# Test for validation bypass with special types
@given(st.one_of(
    st.complex_numbers(),
    st.decimals(allow_nan=False, allow_infinity=False),
    st.fractions(),
))
def test_integer_function_special_numeric_types(val):
    """Test integer function with special numeric types"""
    try:
        result = sl.integer(val)
        # If it accepts these types, document the behavior
        print(f"Accepted {type(val).__name__}: {val} -> {result}")
    except (ValueError, TypeError) as e:
        # Expected to reject these types
        pass


# Test property validation with None
def test_required_property_none_handling():
    """Test that required properties properly reject None"""
    # DataLakeArn is required
    try:
        source = sl.AwsLogSource(
            'Test',
            DataLakeArn=None,  # Required field with None
            SourceName='test',
            SourceVersion='1.0'
        )
        result = source.to_dict()
        # If this succeeds, None was accepted for a required field
        assert False, f"Required field DataLakeArn accepted None: {result}"
    except (TypeError, AttributeError) as e:
        pass  # Expected


# Test with extremely long strings
@given(st.integers(min_value=1000, max_value=1000000))
def test_large_string_handling(length):
    """Test handling of very large strings"""
    # Create a large string
    large_str = 'a' * length
    
    source = sl.AwsLogSource(
        'Test',
        DataLakeArn=large_str,
        SourceName=large_str,
        SourceVersion=large_str
    )
    
    result = source.to_dict()
    # Should handle large strings
    assert len(result['Properties']['DataLakeArn']) == length


# Test mutation side effects
@given(st.lists(st.text(), min_size=1))
def test_list_property_mutation_safety(accounts):
    """Test that list properties are safely stored"""
    original_accounts = accounts.copy()
    
    source = sl.AwsLogSource(
        'Test',
        DataLakeArn='test',
        SourceName='test',
        SourceVersion='1.0',
        Accounts=accounts
    )
    
    # Mutate the original list
    accounts.append('MUTATED')
    
    # Check if the mutation affected the stored value
    result = source.to_dict()
    if result['Properties']['Accounts'] != original_accounts:
        # The mutation affected the internal state - potential bug
        assert False, f"External mutation affected internal state: {result['Properties']['Accounts']}"


# Test nested property validation
@given(st.dictionaries(st.text(), st.text()))
def test_nested_property_dict_coercion(d):
    """Test if dict can be coerced to nested properties"""
    try:
        # Try to pass a dict instead of EncryptionConfiguration object
        lake = sl.DataLake(
            'Test',
            EncryptionConfiguration=d  # Pass dict instead of object
        )
        result = lake.to_dict()
        # If this succeeds, type validation was bypassed
        assert False, f"Dict was accepted instead of EncryptionConfiguration: {result}"
    except TypeError:
        pass  # Expected


# Test property name case sensitivity
def test_property_case_sensitivity():
    """Test if properties are case-sensitive"""
    try:
        # Try wrong case for property
        source = sl.AwsLogSource(
            'Test',
            datalakearn='test',  # lowercase instead of DataLakeArn
            SourceName='test',
            SourceVersion='1.0'
        )
        # If this succeeds, case-insensitive matching might be happening
        result = source.to_dict()
        assert False, f"Case-insensitive property accepted: {result}"
    except (TypeError, AttributeError):
        pass  # Expected


# Test validation of Transitions StorageClass
@given(st.text())
def test_transitions_storage_class_validation(storage_class):
    """Test if StorageClass validates against AWS storage classes"""
    trans = sl.Transitions(
        Days=7,
        StorageClass=storage_class
    )
    
    result = trans.to_dict()
    # Any string is accepted - no validation against valid AWS storage classes
    assert result['StorageClass'] == storage_class
    
    # Valid classes should be like: GLACIER, DEEP_ARCHIVE, etc.
    # But the code accepts any string


# Test circular reference handling
def test_circular_reference():
    """Test handling of circular references in nested properties"""
    enc1 = sl.EncryptionConfiguration(KmsKeyId='key1')
    enc2 = sl.EncryptionConfiguration(KmsKeyId='key2')
    
    lake1 = sl.DataLake('Lake1', EncryptionConfiguration=enc1)
    lake2 = sl.DataLake('Lake2', EncryptionConfiguration=enc1)  # Reuse same object
    
    dict1 = lake1.to_dict()
    dict2 = lake2.to_dict()
    
    # Modify enc1
    enc1.KmsKeyId = 'modified'
    
    # Check if both lakes are affected
    dict1_after = lake1.to_dict()
    dict2_after = lake2.to_dict()
    
    if dict1_after['Properties']['EncryptionConfiguration']['KmsKeyId'] == 'modified':
        # Shared reference - modifications affect all users
        assert dict2_after['Properties']['EncryptionConfiguration']['KmsKeyId'] == 'modified'


# Test with Unicode and special characters
@given(st.text(
    alphabet=st.characters(whitelist_categories=['Zs', 'Cc', 'Cf']),
    min_size=1
))
def test_unicode_special_characters(text):
    """Test handling of Unicode whitespace and control characters"""
    source = sl.AwsLogSource(
        'Test',
        DataLakeArn=text,
        SourceName=text,
        SourceVersion=text
    )
    
    result = source.to_dict()
    # Should preserve special characters exactly
    assert result['Properties']['DataLakeArn'] == text


# Test integer overflow
@given(st.integers())
def test_expiration_days_integer_overflow(days):
    """Test Expiration Days with very large integers"""
    try:
        exp = sl.Expiration(Days=days)
        result = exp.to_dict()
        assert result['Days'] == days
        
        # Try JSON serialization
        json_str = json.dumps(result)
        parsed = json.loads(json_str)
        
        # Check if the value survived JSON round-trip
        if parsed['Days'] != days:
            # JSON serialization changed the value - potential overflow
            print(f"Integer {days} became {parsed['Days']} after JSON round-trip")
    except (OverflowError, ValueError):
        # Some integers might be too large
        pass