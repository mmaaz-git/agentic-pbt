"""Property-based tests for pydantic.fields module."""

import math
from typing import Any, Dict, List, Union

from hypothesis import assume, given, settings, strategies as st
from pydantic import BaseModel, Field, ValidationError
from pydantic.fields import AliasPath, FieldInfo


# Strategy for generating valid path elements (strings or integers)
path_element = st.one_of(
    st.text(min_size=1, max_size=10, alphabet=st.characters(min_codepoint=97, max_codepoint=122)),
    st.integers(min_value=0, max_value=10)
)


# Property 1: Fields with contradictory numeric constraints should never validate
@given(
    gt=st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10),
    lt=st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10),
    test_value=st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10)
)
def test_contradictory_gt_lt_constraints(gt: float, lt: float, test_value: float):
    """If gt >= lt, no value should satisfy both constraints."""
    assume(gt >= lt)  # Only test contradictory constraints
    
    class TestModel(BaseModel):
        value: float = Field(gt=gt, lt=lt)
    
    # No value should be accepted when gt >= lt
    try:
        instance = TestModel(value=test_value)
        # If we get here, a value was accepted despite contradictory constraints
        assert False, f"Value {test_value} was accepted with gt={gt}, lt={lt}"
    except ValidationError:
        # This is expected - contradictory constraints should reject all values
        pass


# Property 2: Fields with contradictory min/max length should never validate
@given(
    min_len=st.integers(min_value=0, max_value=1000),
    max_len=st.integers(min_value=0, max_value=1000),
    test_string=st.text(min_size=0, max_size=2000)
)
def test_contradictory_length_constraints(min_len: int, max_len: int, test_string: str):
    """If min_length > max_length, no string should satisfy both constraints."""
    assume(min_len > max_len)  # Only test contradictory constraints
    
    class TestModel(BaseModel):
        value: str = Field(min_length=min_len, max_length=max_len)
    
    # No string should be accepted when min_length > max_length
    try:
        instance = TestModel(value=test_string)
        assert False, f"String of length {len(test_string)} was accepted with min_length={min_len}, max_length={max_len}"
    except ValidationError:
        # Expected - contradictory constraints should reject all values
        pass


# Property 3: AliasPath.search_dict_for_path should handle out-of-bounds gracefully
@given(
    list_size=st.integers(min_value=0, max_value=10),
    index=st.integers(min_value=0, max_value=100),
    nested_key=st.text(min_size=1, max_size=5, alphabet=st.characters(min_codepoint=97, max_codepoint=122))
)
def test_aliaspath_out_of_bounds(list_size: int, index: int, nested_key: str):
    """AliasPath should return PydanticUndefined for out-of-bounds indices."""
    # Create a list with the specified size
    test_list = [{"key": f"value_{i}"} for i in range(list_size)]
    test_dict = {"items": test_list}
    
    # Create path that tries to access index
    path = AliasPath("items", index, nested_key)
    result = path.search_dict_for_path(test_dict)
    
    if index < list_size:
        # Should find something if index is valid
        assert result != "PydanticUndefined", f"Valid index {index} returned undefined"
    else:
        # Should return PydanticUndefined for out-of-bounds
        assert str(type(result).__name__) == "PydanticUndefinedType", f"Out-of-bounds index {index} didn't return PydanticUndefined"


# Property 4: FieldInfo.merge_field_infos should be associative
@given(
    defaults=st.lists(st.one_of(st.none(), st.integers(), st.text()), min_size=3, max_size=3),
    descriptions=st.lists(st.one_of(st.none(), st.text(min_size=1, max_size=10)), min_size=3, max_size=3),
    titles=st.lists(st.one_of(st.none(), st.text(min_size=1, max_size=10)), min_size=3, max_size=3)
)
def test_fieldinfo_merge_associativity(defaults: List[Any], descriptions: List[Any], titles: List[Any]):
    """Merging FieldInfos should be associative: (a+b)+c == a+(b+c)."""
    # Create three FieldInfo instances with different attributes
    field_infos = []
    for i in range(3):
        kwargs = {}
        if defaults[i] is not None:
            kwargs['default'] = defaults[i]
        if descriptions[i] is not None:
            kwargs['description'] = descriptions[i]
        if titles[i] is not None:
            kwargs['title'] = titles[i]
        field_infos.append(FieldInfo(**kwargs))
    
    f1, f2, f3 = field_infos
    
    # Test associativity: (f1 + f2) + f3 == f1 + (f2 + f3)
    left_assoc = FieldInfo.merge_field_infos(
        FieldInfo.merge_field_infos(f1, f2), f3
    )
    right_assoc = FieldInfo.merge_field_infos(
        f1, FieldInfo.merge_field_infos(f2, f3)
    )
    
    # Check that key attributes are the same
    assert left_assoc.default == right_assoc.default, f"Defaults differ: {left_assoc.default} != {right_assoc.default}"
    assert left_assoc.description == right_assoc.description, f"Descriptions differ: {left_assoc.description} != {right_assoc.description}"
    assert left_assoc.title == right_assoc.title, f"Titles differ: {left_assoc.title} != {right_assoc.title}"


# Property 5: AliasPath should correctly traverse nested structures
@given(
    path_elements=st.lists(path_element, min_size=1, max_size=5)
)
@settings(max_examples=100)
def test_aliaspath_traversal_correctness(path_elements: List[Union[str, int]]):
    """AliasPath should correctly traverse nested dictionaries and lists."""
    # Build a nested structure that matches the path
    result = "final_value"
    nested = result
    
    # Build structure backwards from the path
    for element in reversed(path_elements):
        if isinstance(element, int):
            # Create a list with the element at the right index
            new_list = [None] * (element + 1)
            new_list[element] = nested
            nested = new_list
        else:
            # Create a dict with the element as key
            nested = {element: nested}
    
    # Now traverse with AliasPath
    path = AliasPath(*path_elements)
    
    # The first element must be a string for search_dict_for_path
    if isinstance(path_elements[0], int):
        # Wrap in a dict with integer as string key
        nested = {str(path_elements[0]): nested[path_elements[0]]}
        path = AliasPath(str(path_elements[0]), *path_elements[1:])
    
    found = path.search_dict_for_path(nested)
    assert found == result, f"Path {path_elements} didn't find correct value. Got {found}, expected {result}"


# Property 6: Field with multiple_of constraint
@given(
    multiple_of=st.floats(min_value=0.1, max_value=100.0, allow_nan=False, allow_infinity=False),
    multiplier=st.integers(min_value=-100, max_value=100)
)
def test_field_multiple_of_accepts_multiples(multiple_of: float, multiplier: int):
    """Field with multiple_of constraint should accept exact multiples."""
    class TestModel(BaseModel):
        value: float = Field(multiple_of=multiple_of)
    
    test_value = multiple_of * multiplier
    
    # Exact multiples should be accepted
    try:
        instance = TestModel(value=test_value)
        assert math.isclose(instance.value, test_value), f"Value changed from {test_value} to {instance.value}"
    except ValidationError as e:
        # This could be due to floating point precision issues
        # Check if it's really not a multiple
        remainder = abs(test_value % multiple_of)
        if remainder > 1e-10 * abs(multiple_of):
            raise AssertionError(f"Valid multiple {test_value} of {multiple_of} was rejected") from e


# Property 7: Field constraints interaction - ge/le
@given(
    ge=st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10),
    le=st.floats(allow_nan=False, allow_infinity=False, min_value=-1e10, max_value=1e10)
)
def test_ge_le_constraints_boundary(ge: float, le: float):
    """Fields with ge and le should accept values at the boundaries."""
    assume(ge <= le)  # Only test valid constraints
    
    class TestModel(BaseModel):
        value: float = Field(ge=ge, le=le)
    
    # Boundary values should be accepted
    for test_value in [ge, le]:
        instance = TestModel(value=test_value)
        assert instance.value == test_value, f"Boundary value {test_value} was modified"