import pytest
from hypothesis import given, settings, strategies as st

import troposphere.quicksight as qs


# Test edge cases for boolean validator
@given(st.one_of(
    # Test string variations
    st.sampled_from(["TRUE", "True ", " true", "true\n", "1.0", "01", "00", "FALSE", "False ", " false"]),
    # Test numeric edge cases
    st.sampled_from([1.0, 0.0, -0, -1, 2, 0.1, -0.0]),
    # Test byte strings
    st.sampled_from([b"true", b"false", b"1", b"0"]),
))
def test_boolean_edge_cases(value):
    """Test edge cases for boolean validator."""
    try:
        result = qs.boolean(value)
        # If it succeeds, check it returns correct boolean
        if value in [True, 1, "1", "true", "True", 1.0]:
            assert result is True
        elif value in [False, 0, "0", "false", "False", 0.0, -0]:
            assert result is False
        else:
            # If it succeeded but value is not in known list, this is interesting
            print(f"Unexpected success for value: {value!r} -> {result}")
    except ValueError:
        # Expected for invalid values
        pass


# Test edge cases for double validator
@given(st.one_of(
    # Special float strings
    st.sampled_from(["inf", "-inf", "nan", "NaN", "Infinity", "-Infinity"]),
    # Scientific notation edge cases
    st.sampled_from(["1e308", "1e-308", "1e309", "-1e309", "1e-400"]),
    # Numeric string edge cases  
    st.sampled_from(["+0", "-0", "00", "001", "+1", ".5", "5.", "1,000", "1_000"]),
    # Bytes
    st.sampled_from([b"3.14", b"0", b"inf"]),
    # Boolean
    st.booleans(),
))
def test_double_edge_cases(value):
    """Test edge cases for double validator."""
    try:
        # Try what double does
        result = qs.double(value)
        
        # If it succeeds, verify float conversion works
        float_val = float(value)
        
        # The function should return the original value unchanged
        assert result == value
    except ValueError:
        # Expected for invalid values
        # But let's check if float() would also fail
        try:
            float(value)
            # If float() succeeds but double() fails, that's a bug!
            print(f"BUG: float({value!r}) succeeds but double({value!r}) fails")
            assert False, f"double() incorrectly rejects {value!r}"
        except (ValueError, TypeError):
            # Both fail, that's consistent
            pass


# Test complex nested structures
@given(
    st.recursive(
        st.dictionaries(st.text(min_size=1, max_size=5), st.text(min_size=0, max_size=10), max_size=3),
        lambda children: st.dictionaries(st.text(min_size=1, max_size=5), children, max_size=3),
        max_leaves=10
    )
)
def test_nested_dict_round_trip(data):
    """Test round-trip with complex nested dictionaries."""
    try:
        # Try with DefaultInteractiveLayoutConfiguration which has nested structure
        obj = qs.DefaultInteractiveLayoutConfiguration.from_dict("Test", data)
        dict1 = obj.to_dict(validation=False)
        obj2 = qs.DefaultInteractiveLayoutConfiguration.from_dict("Test2", dict1)
        dict2 = obj2.to_dict(validation=False)
        
        assert dict1 == dict2
    except (TypeError, KeyError, AttributeError):
        # Expected for invalid structures
        pass


# Test property inheritance and complex class relationships
@given(
    st.dictionaries(
        st.sampled_from(["Type", "Properties", "Condition", "DependsOn", "Metadata", "DeletionPolicy"]),
        st.text(min_size=1, max_size=10),
        min_size=1
    )
)
def test_aws_object_attributes(data):
    """Test that AWSObject subclasses handle standard CloudFormation attributes."""
    # Analysis is an AWSObject (not just AWSProperty)
    try:
        obj = qs.Analysis.from_dict("TestAnalysis", data)
        dict1 = obj.to_dict(validation=False)
        
        # Check if Type is preserved for AWSObject
        if "Type" in data:
            assert "Type" in dict1 or hasattr(obj, "resource_type")
            
    except (TypeError, KeyError, AttributeError) as e:
        # Some attributes might be rejected
        pass


# Test with unicode and special characters  
@given(
    st.dictionaries(
        st.text(alphabet=["🦄", "😀", "λ", "∞", "π", "α", "β", "γ"], min_size=1, max_size=5),
        st.text(min_size=1, max_size=10),
        min_size=1
    )
)
def test_unicode_property_names(data):
    """Test handling of unicode characters in property names."""
    try:
        obj = qs.Spacing(**data)
        # Should likely fail with non-ASCII property names
    except (TypeError, AttributeError, KeyError):
        # Expected for invalid property names
        pass


# Test validator with None and empty values
@given(st.sampled_from([None, "", [], {}, (), set()]))
def test_validators_with_empty_values(value):
    """Test how validators handle None and empty values."""
    # Test boolean
    try:
        result = qs.boolean(value)
        print(f"Unexpected: boolean({value!r}) = {result}")
    except (ValueError, TypeError):
        pass  # Expected
    
    # Test double
    try:
        result = qs.double(value)
        print(f"Unexpected: double({value!r}) = {result}")
    except (ValueError, TypeError):
        pass  # Expected


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])