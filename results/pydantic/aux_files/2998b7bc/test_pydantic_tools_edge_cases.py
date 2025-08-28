import json
import warnings
from typing import Dict, List, Optional, Union, Tuple, Any, Set, FrozenSet
from decimal import Decimal
from hypothesis import given, strategies as st, settings, assume, note
from pydantic.tools import parse_obj_as, schema_of, schema_json_of
from pydantic import TypeAdapter
from pydantic.warnings import PydanticDeprecatedSince20
import math

# Suppress deprecation warnings for testing
warnings.filterwarnings("ignore", category=PydanticDeprecatedSince20)


# Test edge case: Unicode and special characters
@given(
    text=st.text(alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Lt", "Nd", "Po", "Sc", "So")), min_size=1, max_size=100)
)
def test_unicode_handling(text):
    """Test that unicode strings are handled correctly."""
    result = parse_obj_as(str, text)
    assert result == text
    assert isinstance(result, str)
    
    # Test in lists
    result_list = parse_obj_as(List[str], [text])
    assert result_list == [text]
    
    # Test in dicts
    result_dict = parse_obj_as(Dict[str, str], {text: text})
    assert result_dict == {text: text}


# Test edge case: Numeric boundaries
@given(
    num=st.one_of(
        st.just(0),
        st.just(-0.0),
        st.just(float('inf')),
        st.just(float('-inf')),
        st.floats(min_value=float('-inf'), max_value=float('inf')),
        st.floats(min_value=1e308, max_value=1.7e308),  # Near float max
        st.floats(min_value=-1.7e308, max_value=-1e308)  # Near float min
    )
)
def test_numeric_edge_cases(num):
    """Test edge case numeric values."""
    if math.isfinite(num):
        result = parse_obj_as(float, num)
        if math.isnan(num):
            assert math.isnan(result)
        else:
            assert result == num
    else:
        # Infinity values
        result = parse_obj_as(float, num)
        assert math.isinf(result) == math.isinf(num)
        if math.isinf(num):
            assert result == num


# Test edge case: Empty collections
@given(
    collection_type=st.sampled_from([list, dict, set, frozenset, tuple])
)
def test_empty_collections(collection_type):
    """Test that empty collections are handled correctly."""
    if collection_type == list:
        result = parse_obj_as(List[int], [])
        assert result == []
        assert isinstance(result, list)
    elif collection_type == dict:
        result = parse_obj_as(Dict[str, int], {})
        assert result == {}
        assert isinstance(result, dict)
    elif collection_type == set:
        result = parse_obj_as(Set[int], set())
        assert result == set()
        assert isinstance(result, set)
    elif collection_type == frozenset:
        result = parse_obj_as(FrozenSet[int], frozenset())
        assert result == frozenset()
        assert isinstance(result, frozenset)
    elif collection_type == tuple:
        result = parse_obj_as(Tuple[()], ())
        assert result == ()
        assert isinstance(result, tuple)


# Test edge case: None in Optional types
@given(
    type_=st.sampled_from([int, str, float, bool, list, dict]),
    use_none=st.booleans()
)
def test_optional_none_handling(type_, use_none):
    """Test Optional type handling with None values."""
    optional_type = Optional[type_]
    
    if use_none:
        result = parse_obj_as(optional_type, None)
        assert result is None
    else:
        # Use a simple default value for the type
        if type_ == int:
            value = 42
        elif type_ == str:
            value = "test"
        elif type_ == float:
            value = 3.14
        elif type_ == bool:
            value = True
        elif type_ == list:
            value = []
        else:  # dict
            value = {}
        
        result = parse_obj_as(optional_type, value)
        assert result == value


# Test edge case: Deeply nested structures
@given(depth=st.integers(min_value=1, max_value=10))
def test_deeply_nested_structures(depth):
    """Test parsing of deeply nested data structures."""
    # Build nested list type
    type_ = int
    value = 42
    for _ in range(depth):
        type_ = List[type_]
        value = [value]
    
    result = parse_obj_as(type_, value)
    assert result == value


# Test edge case: Large strings in schema
@given(
    size=st.integers(min_value=0, max_value=10000)
)
@settings(max_examples=20)
def test_large_string_schema(size):
    """Test schema generation with large strings."""
    text = "x" * size
    
    # Create a class with a large default value
    from typing import Literal
    
    try:
        if size <= 100:  # Literal types have size limitations
            literal_type = Literal[text]
            schema = schema_of(literal_type)
            assert 'const' in schema or 'enum' in schema
    except Exception:
        # Some literal values might be too large
        pass


# Test edge case: Special dictionary keys
@given(
    key=st.one_of(
        st.text(min_size=0, max_size=100),
        st.text(alphabet="", min_size=1, max_size=10),  # Empty string repeated
        st.text(alphabet=" \t\n\r", min_size=1, max_size=10),  # Whitespace only
    )
)
def test_special_dict_keys(key):
    """Test dictionaries with special keys."""
    value = {"regular": 1, key: 2}
    result = parse_obj_as(Dict[str, int], value)
    assert result == value
    assert len(result) == 2 if key != "regular" else 1


# Test edge case: Coercion edge cases
@given(
    value=st.one_of(
        st.just("1"),
        st.just("0"),
        st.just("-1"),
        st.just("true"),
        st.just("false"),
        st.just("True"),
        st.just("False"),
        st.just("1.0"),
        st.just("0.0"),
        st.just(""),
        st.just(" "),
    )
)
def test_string_to_type_coercion(value):
    """Test string coercion to various types."""
    # Test int coercion
    try:
        result = parse_obj_as(int, value)
        # Should succeed for numeric strings
        assert isinstance(result, int)
    except Exception:
        # Non-numeric strings should fail
        pass
    
    # Test bool coercion  
    try:
        result = parse_obj_as(bool, value)
        # Pydantic has specific bool conversion rules
        assert isinstance(result, bool)
    except Exception:
        pass
    
    # Test float coercion
    try:
        result = parse_obj_as(float, value)
        assert isinstance(result, float)
    except Exception:
        pass


# Test edge case: Mixed type lists
@given(
    items=st.lists(
        st.one_of(
            st.integers(),
            st.text(max_size=10),
            st.floats(allow_nan=False, allow_infinity=False),
            st.booleans(),
            st.none()
        ),
        min_size=0,
        max_size=20
    )
)
def test_union_type_lists(items):
    """Test lists with Union types."""
    # Union of all possible types in the list
    union_type = List[Union[int, str, float, bool, None]]
    
    result = parse_obj_as(union_type, items)
    assert len(result) == len(items)
    
    # Check each item is preserved correctly (accounting for bool/int relationship in Python)
    for orig, parsed in zip(items, result):
        if isinstance(orig, bool):
            # In Python, bool is a subtype of int, so this needs special handling
            assert parsed == orig
        elif orig is None:
            assert parsed is None
        else:
            assert parsed == orig


# Test edge case: Type name parameter (deprecated feature)
@given(
    type_hint=st.sampled_from([int, str, float, bool]),
    type_name=st.one_of(
        st.none(),
        st.text(min_size=1, max_size=50),
        st.just(lambda t: f"Custom_{t.__name__}")  # Callable type name
    )
)
def test_type_name_parameter(type_hint, type_name):
    """Test the deprecated type_name parameter."""
    # Choose appropriate value for each type
    if type_hint == int:
        value = "42"
    elif type_hint == float:
        value = "3.14"
    elif type_hint == bool:
        value = "true"
    else:  # str
        value = "test"
    
    if callable(type_name):
        # Callable type names should trigger a deprecation warning
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = parse_obj_as(type_hint, value, type_name=type_name)
            # Should have deprecation warning
            assert any("type_name parameter is deprecated" in str(warning.message) for warning in w)
    else:
        # String or None type names
        result = parse_obj_as(type_hint, value, type_name=type_name)