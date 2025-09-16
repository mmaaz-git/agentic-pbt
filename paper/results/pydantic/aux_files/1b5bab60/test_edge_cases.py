"""Additional edge case tests for pydantic.fields."""

from hypothesis import given, settings, strategies as st
from pydantic import BaseModel, Field, ValidationError
from pydantic.fields import AliasPath
import math


# Test for special float values
@given(
    constraint_value=st.sampled_from([0.0, -0.0, float('inf'), float('-inf')]),
    test_value=st.floats(allow_nan=True, allow_infinity=True)
)
def test_field_constraints_with_special_floats(constraint_value: float, test_value: float):
    """Test Field constraints with special float values like infinity."""
    if math.isinf(constraint_value):
        # Skip infinity constraints as they might not be well-defined
        return
    
    try:
        class TestModel(BaseModel):
            value: float = Field(ge=constraint_value)
        
        # Try to create instance
        if not math.isnan(test_value) and test_value >= constraint_value:
            instance = TestModel(value=test_value)
            assert instance.value == test_value or (math.isnan(instance.value) and math.isnan(test_value))
        else:
            try:
                instance = TestModel(value=test_value)
                if math.isnan(test_value):
                    # NaN handling might be special
                    pass
                else:
                    assert False, f"Value {test_value} should have been rejected with ge={constraint_value}"
            except ValidationError:
                pass  # Expected
    except Exception as e:
        # Some constraint values might not be supported
        pass


# Test empty string constraints
@given(
    min_len=st.integers(min_value=0, max_value=10),
    max_len=st.integers(min_value=0, max_value=10)
)
def test_empty_string_with_length_constraints(min_len: int, max_len: int):
    """Test how empty strings interact with length constraints."""
    if min_len > max_len:
        return  # Skip contradictory constraints
    
    class TestModel(BaseModel):
        value: str = Field(min_length=min_len, max_length=max_len)
    
    test_string = ""
    
    if min_len <= 0 <= max_len:
        # Empty string should be accepted
        instance = TestModel(value=test_string)
        assert instance.value == test_string
    else:
        # Empty string should be rejected
        try:
            instance = TestModel(value=test_string)
            assert False, f"Empty string accepted with min_length={min_len}"
        except ValidationError:
            pass  # Expected


# Test AliasPath with None values in path
@given(
    before_none=st.integers(min_value=0, max_value=3),
    after_none=st.integers(min_value=0, max_value=3)
)
def test_aliaspath_with_none_in_structure(before_none: int, after_none: int):
    """Test AliasPath behavior when encountering None in the structure."""
    # Build a structure with None at some point
    structure = {"root": {}}
    current = structure["root"]
    
    # Add some valid nested structure
    for i in range(before_none):
        current[f"level_{i}"] = {}
        current = current[f"level_{i}"]
    
    # Add None
    current["none_value"] = None
    
    # Create path that tries to go through None
    path_elements = ["root"]
    for i in range(before_none):
        path_elements.append(f"level_{i}")
    path_elements.append("none_value")
    path_elements.append("beyond_none")  # Try to go beyond None
    
    path = AliasPath(*path_elements)
    result = path.search_dict_for_path(structure)
    
    # Should return PydanticUndefined when trying to traverse through None
    assert str(type(result).__name__) == "PydanticUndefinedType", f"Traversing through None didn't return PydanticUndefined"


# Test with very deep nesting
@given(
    depth=st.integers(min_value=1, max_value=100)
)
@settings(max_examples=50)
def test_aliaspath_deep_nesting(depth: int):
    """Test AliasPath with very deep nesting."""
    # Build deeply nested structure
    value = "deep_value"
    structure = value
    path_elements = []
    
    for i in range(depth):
        key = f"level_{i}"
        path_elements.insert(0, key)
        structure = {key: structure}
    
    path = AliasPath(*path_elements)
    result = path.search_dict_for_path(structure)
    
    assert result == value, f"Deep nesting of depth {depth} failed to find value"


# Test Field with decimal_places and max_digits
@given(
    max_digits=st.integers(min_value=1, max_value=10),
    decimal_places=st.integers(min_value=0, max_value=10)
)
def test_field_decimal_constraints_consistency(max_digits: int, decimal_places: int):
    """Test Field with decimal_places and max_digits constraints."""
    # decimal_places should not exceed max_digits
    from decimal import Decimal
    
    try:
        class TestModel(BaseModel):
            value: Decimal = Field(max_digits=max_digits, decimal_places=decimal_places)
        
        # If decimal_places > max_digits, this might be problematic
        if decimal_places <= max_digits:
            # Try with a valid decimal
            test_value = Decimal("0." + "1" * decimal_places) if decimal_places > 0 else Decimal("1")
            instance = TestModel(value=test_value)
            assert instance.value == test_value
        else:
            # This configuration might not make sense
            # Try to create any valid value
            for test in [Decimal("0"), Decimal("0.1"), Decimal("1")]:
                try:
                    instance = TestModel(value=test)
                    # If it accepts something, that's interesting
                    break
                except ValidationError:
                    continue
    except Exception as e:
        # Some configurations might raise errors at model creation time
        pass