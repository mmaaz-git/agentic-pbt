import sys
sys.path.insert(0, './venv/lib/python3.13/site-packages')

import pytest
from hypothesis import given, strategies as st, assume, settings
from hypothesis.strategies import composite
import troposphere.lakeformation as lf
from troposphere.lakeformation import *
from troposphere import AWSObject, AWSProperty
from troposphere.validators import boolean


# Test 1: Boolean validator case-insensitivity property
# The function claims to convert string values to boolean, and it should handle
# case variations consistently
@given(st.sampled_from(["true", "false"]))
def test_boolean_validator_case_insensitive(base_value):
    """The boolean validator should handle case variations of 'true' and 'false' consistently."""
    # Generate case variations
    variations = [
        base_value,
        base_value.upper(),
        base_value.lower(),
        base_value.capitalize(),
        base_value.title(),
    ]
    
    # All variations should produce the same result
    results = []
    for variant in variations:
        try:
            result = boolean(variant)
            results.append(("success", result))
        except ValueError:
            results.append(("error", None))
    
    # Check if all results are consistent - they should all succeed or all fail
    # Based on the code, we know lowercase and Title case work, but UPPER doesn't
    # This reveals the inconsistency
    first_result = results[0]
    for i, result in enumerate(results):
        if result != first_result:
            # Found inconsistency - the validator is case-sensitive when it shouldn't be
            raise AssertionError(
                f"Boolean validator is inconsistent with case variations of '{base_value}': "
                f"'{variations[0]}' -> {results[0]}, but '{variations[i]}' -> {result}"
            )


# Test 2: Type validation for list properties
@given(st.lists(st.integers()))
def test_column_wildcard_type_validation(int_list):
    """ColumnWildcard should reject lists of non-strings."""
    assume(len(int_list) > 0)  # Only test non-empty lists
    
    # ColumnWildcard expects list of strings
    try:
        cw = ColumnWildcard(ExcludedColumnNames=int_list)
        # If it accepts integers, that's a type validation bug
        # Let's check if to_dict preserves the wrong type
        result = cw.to_dict()
        # The validator should have rejected this during construction
        assert False, f"ColumnWildcard accepted list of integers: {int_list}"
    except TypeError as e:
        # This is expected - type validation working correctly
        assert "expected [<class 'str'>]" in str(e)


# Test 3: Round-trip property for classes with from_dict
@composite
def valid_datacellsfilter_data(draw):
    """Generate valid DataCellsFilter data."""
    return {
        "DatabaseName": draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=["Lu", "Ll", "Nd"]))),
        "Name": draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=["Lu", "Ll", "Nd"]))),
        "TableCatalogId": draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=["Nd"]))),
        "TableName": draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=["Lu", "Ll", "Nd"]))),
    }


@given(valid_datacellsfilter_data())
def test_datacellsfilter_roundtrip(data):
    """DataCellsFilter should support to_dict/from_dict round-trip."""
    # Create a DataCellsFilter with valid data
    title = "TestFilter"
    dcf = DataCellsFilter(title, **data)
    
    # Convert to dict
    dict_repr = dcf.to_dict()
    
    # Try to reconstruct from dict
    try:
        # Check if from_dict exists and works
        reconstructed = DataCellsFilter.from_dict(title, dict_repr)
        
        # The round-trip should preserve the data
        reconstructed_dict = reconstructed.to_dict()
        
        # Check if the Properties are preserved
        if "Properties" in dict_repr and "Properties" in reconstructed_dict:
            original_props = dict_repr["Properties"]
            reconstructed_props = reconstructed_dict["Properties"]
            
            for key in data:
                assert key in original_props, f"Key {key} missing from original dict"
                assert key in reconstructed_props, f"Key {key} missing from reconstructed dict"
                assert original_props[key] == reconstructed_props[key], \
                    f"Round-trip failed for {key}: {original_props[key]} != {reconstructed_props[key]}"
    except AttributeError as e:
        if "Properties property" in str(e):
            # This is the known issue with from_dict
            raise AssertionError(
                f"from_dict fails with 'Properties property' error. "
                f"Original dict: {dict_repr}"
            )
        raise


# Test 4: Boolean validator with numeric edge cases
@given(st.integers())
def test_boolean_validator_numeric_consistency(num):
    """Boolean validator should handle numeric values consistently."""
    # According to the code, only 0 and 1 should work
    try:
        result = boolean(num)
        # Should only succeed for 0 or 1
        assert num in [0, 1], f"Boolean validator accepted invalid number: {num} -> {result}"
        # Verify the result is correct
        expected = True if num == 1 else False
        assert result == expected, f"Boolean validator returned wrong value for {num}: {result}"
    except ValueError:
        # Should fail for anything other than 0 or 1
        assert num not in [0, 1], f"Boolean validator rejected valid number: {num}"


# Test 5: Empty props validation
@given(st.dictionaries(st.text(), st.text()))
def test_tablewildcard_empty_props(extra_params):
    """TableWildcard with empty props should reject any parameters."""
    assume(len(extra_params) > 0)  # Only test with actual parameters
    
    # TableWildcard has empty props dictionary
    try:
        tw = TableWildcard(**extra_params)
        # If it accepts parameters, that's unexpected
        raise AssertionError(f"TableWildcard accepted unexpected parameters: {extra_params}")
    except AttributeError as e:
        # This is expected
        assert "does not support attribute" in str(e)


# Test 6: Required field validation
@given(st.text(min_size=1, max_size=20))
def test_required_field_validation(title):
    """Classes should validate required fields on to_dict()."""
    assume(title.replace(" ", "").isalnum())  # Title must be alphanumeric
    
    # Create DataCellsFilter without required fields
    dcf = DataCellsFilter(title)
    
    # to_dict should fail validation
    try:
        result = dcf.to_dict()
        raise AssertionError(f"to_dict() succeeded without required fields: {result}")
    except ValueError as e:
        # Should mention a required field
        assert "required in type" in str(e)


if __name__ == "__main__":
    # Run a quick test to see if we find any issues
    print("Running property-based tests...")
    
    # Test the boolean validator case sensitivity
    try:
        test_boolean_validator_case_insensitive("true")
        print("✓ Boolean validator case sensitivity test passed")
    except AssertionError as e:
        print(f"✗ Boolean validator case sensitivity test failed: {e}")
    
    # Test numeric consistency
    try:
        for num in [0, 1, 2, -1]:
            test_boolean_validator_numeric_consistency(num)
        print("✓ Boolean validator numeric test passed")
    except AssertionError as e:
        print(f"✗ Boolean validator numeric test failed: {e}")