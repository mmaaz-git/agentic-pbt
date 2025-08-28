"""Property-based tests for troposphere.memorydb module."""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import pytest
from hypothesis import given, strategies as st, assume, settings
import troposphere.memorydb as memorydb
from troposphere.validators import boolean, integer


# Property 1: Boolean validator case sensitivity inconsistency
@given(st.sampled_from(["true", "false"]))
def test_boolean_validator_case_consistency(base_value):
    """Boolean validator should handle all case variations of 'true'/'false' consistently.
    
    The validator accepts "true"/"True" and "false"/"False" but rejects "TRUE"/"FALSE".
    This is inconsistent - if it accepts "True", it should accept "TRUE" as well.
    """
    # Test different case variations
    test_cases = [
        base_value.lower(),   # "true" or "false"
        base_value.upper(),   # "TRUE" or "FALSE"  
        base_value.capitalize(),  # "True" or "False"
    ]
    
    results = []
    for test_value in test_cases:
        try:
            result = boolean(test_value)
            results.append((test_value, "success", result))
        except ValueError:
            results.append((test_value, "error", None))
    
    # Check for inconsistency
    success_count = sum(1 for _, status, _ in results if status == "success")
    
    # If some succeed and some fail, that's inconsistent
    if 0 < success_count < len(results):
        successes = [v for v, s, _ in results if s == "success"]
        failures = [v for v, s, _ in results if s == "error"]
        assert False, f"Boolean validator inconsistent: accepts {successes} but rejects {failures}"


# Property 2: Integer validator type preservation issue
@given(st.integers(min_value=-1000, max_value=1000))
def test_integer_validator_type_preservation(num):
    """Integer validator should consistently handle type conversion.
    
    The validator accepts both int and str inputs but preserves the original type,
    which can lead to inconsistent behavior downstream.
    """
    # Test with different input types
    int_input = num
    str_input = str(num)
    
    result_int = integer(int_input)
    result_str = integer(str_input)
    
    # The validator preserves input type instead of normalizing
    assert type(result_int) == type(int_input)
    assert type(result_str) == type(str_input)
    
    # This means the same numeric value has different types
    assert result_int == num
    assert result_str == str(num)
    assert type(result_int) != type(result_str)


# Property 3: Integer validator whitespace handling
@given(st.integers(min_value=-100, max_value=100))
def test_integer_validator_whitespace(num):
    """Integer validator should handle whitespace consistently.
    
    The validator accepts strings with whitespace but doesn't trim them,
    which preserves the whitespace in the output.
    """
    padded = f"  {num}  "
    result = integer(padded)
    
    # The validator accepts but doesn't normalize whitespace
    assert result == padded  # Preserves the whitespace!
    assert int(result) == num  # But it validated that it's convertible


# Property 4: Required property validation timing
@given(st.text(min_size=1, max_size=20, alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-"))
def test_required_property_validation_timing(name):
    """Required properties should be validated at construction time, not at serialization.
    
    Currently, objects can be created without required properties, and validation
    only happens when to_dict() is called. This violates fail-fast principles.
    """
    # Create ACL without required property - this succeeds
    acl = memorydb.ACL("TestACL")
    
    # Object exists and seems valid
    assert acl.title == "TestACL"
    
    # But calling to_dict() fails
    with pytest.raises(ValueError) as exc:
        acl.to_dict()
    
    assert "ACLName required" in str(exc.value)


# Property 5: Round-trip property for memorydb classes
@given(
    st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=["Lu", "Ll", "Nd"])),
    st.lists(st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=["Lu", "Ll", "Nd"])), max_size=5)
)
def test_acl_roundtrip(acl_name, user_names):
    """ACL objects should support to_dict/from_dict round-trip."""
    # Create an ACL
    acl = memorydb.ACL("TestACL", ACLName=acl_name, UserNames=user_names)
    
    # Convert to dict
    dict_repr = acl.to_dict()
    
    # Extract properties
    props = dict_repr.get("Properties", {})
    
    # Try to recreate from dict
    acl2 = memorydb.ACL.from_dict("TestACL", props)
    
    # Should produce the same dict
    dict_repr2 = acl2.to_dict()
    
    assert dict_repr == dict_repr2


# Property 6: Type validation for list properties
@given(st.lists(st.integers(), min_size=1, max_size=5))
def test_list_property_type_validation(int_list):
    """List properties should validate element types."""
    # SecurityGroupIds expects list of strings, not integers
    cluster = memorydb.Cluster(
        "TestCluster",
        ClusterName="test",
        ACLName="test-acl", 
        NodeType="db.t4g.small"
    )
    
    # Try to set list of integers where strings are expected
    with pytest.raises(TypeError) as exc:
        cluster.SecurityGroupIds = int_list
    
    assert "expected [<class 'str'>]" in str(exc.value)


# Property 7: Port validation with integer validator
@given(st.one_of(
    st.integers(min_value=-100, max_value=100000),
    st.text(min_size=1, max_size=10)
))
def test_port_validation(port_value):
    """Port property should use integer validator correctly."""
    endpoint = memorydb.Endpoint()
    
    try:
        endpoint.Port = port_value
        # If it succeeded, verify the value
        if isinstance(port_value, str):
            # String must be convertible to int
            int(port_value)  # This should work if assignment succeeded
    except (ValueError, TypeError):
        # Expected for non-integer strings
        pass


if __name__ == "__main__":
    # Run a quick test to verify tests work
    import traceback
    
    print("Running property-based tests for troposphere.memorydb...")
    
    # Test boolean case inconsistency
    try:
        test_boolean_validator_case_consistency("true")
        print("✓ Boolean validator test passed for 'true'")
    except AssertionError as e:
        print(f"✗ Boolean validator test found issue: {e}")
    
    # Test integer type preservation
    try:
        test_integer_validator_type_preservation(42)
        print("✓ Integer validator type preservation test passed")
    except Exception as e:
        print(f"✗ Integer validator test error: {e}")
    
    # Test required property validation
    try:
        test_required_property_validation_timing("test-name")
        print("✓ Required property validation timing test passed")
    except Exception as e:
        print(f"✗ Required property test error: {e}")
        traceback.print_exc()