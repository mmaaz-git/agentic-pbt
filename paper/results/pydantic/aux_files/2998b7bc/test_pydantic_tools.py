import json
import warnings
from typing import Dict, List, Optional, Union, Tuple, Any
from hypothesis import given, strategies as st, settings, assume
from pydantic.tools import parse_obj_as, schema_of, schema_json_of
from pydantic import TypeAdapter
from pydantic.warnings import PydanticDeprecatedSince20

# Suppress deprecation warnings for testing
warnings.filterwarnings("ignore", category=PydanticDeprecatedSince20)


# Strategy for generating type annotations
@st.composite  
def simple_type_annotations(draw):
    """Generate simple type annotations that pydantic can handle."""
    base_types = [int, str, float, bool, bytes]
    type_ = draw(st.sampled_from(base_types))
    
    # Sometimes wrap in containers
    if draw(st.booleans()):
        container = draw(st.sampled_from([List, Dict, Optional]))
        if container == List:
            return List[type_]
        elif container == Dict:
            key_type = draw(st.sampled_from([str, int]))
            return Dict[key_type, type_]
        elif container == Optional:
            return Optional[type_]
    
    return type_


@st.composite
def values_for_type(draw, type_hint):
    """Generate values that match a given type hint."""
    import typing
    
    # Handle Optional types
    if hasattr(type_hint, '__origin__'):
        origin = type_hint.__origin__
        args = getattr(type_hint, '__args__', ())
        
        if origin is Union:
            # Handle Optional (Union with None)
            if type(None) in args:
                non_none_types = [t for t in args if t != type(None)]
                if len(non_none_types) == 1:
                    if draw(st.booleans()):
                        return None
                    return draw(values_for_type(non_none_types[0]))
        
        elif origin is list:
            elem_type = args[0] if args else Any
            return draw(st.lists(values_for_type(elem_type), max_size=5))
        
        elif origin is dict:
            key_type = args[0] if len(args) > 0 else Any
            val_type = args[1] if len(args) > 1 else Any
            return draw(st.dictionaries(
                values_for_type(key_type),
                values_for_type(val_type),
                max_size=5
            ))
    
    # Base types
    if type_hint is int:
        return draw(st.integers(min_value=-10000, max_value=10000))
    elif type_hint is str:
        return draw(st.text(max_size=100))
    elif type_hint is float:
        return draw(st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6))
    elif type_hint is bool:
        return draw(st.booleans())
    elif type_hint is bytes:
        return draw(st.binary(max_size=100))
    
    # Default fallback
    return draw(st.text(max_size=50))


# Property 1: Round-trip between schema_of and schema_json_of
@given(simple_type_annotations())
def test_schema_round_trip(type_hint):
    """Test that schema_of and schema_json_of produce equivalent results."""
    schema_dict = schema_of(type_hint)
    schema_json_str = schema_json_of(type_hint)
    
    # Parse the JSON string back to dict
    schema_from_json = json.loads(schema_json_str)
    
    # They should be identical
    assert schema_dict == schema_from_json, f"Mismatch for type {type_hint}"


# Property 2: parse_obj_as equivalence with TypeAdapter.validate_python  
@given(
    type_hint=simple_type_annotations(),
    value=st.one_of(
        st.integers(min_value=-10000, max_value=10000),
        st.text(max_size=100),
        st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6),
        st.booleans(),
        st.lists(st.integers(), max_size=5),
        st.dictionaries(st.text(max_size=20), st.integers(), max_size=5),
        st.none()
    )
)
def test_parse_obj_as_equivalence(type_hint, value):
    """Test that parse_obj_as behaves identically to TypeAdapter.validate_python."""
    # Test both methods
    adapter = TypeAdapter(type_hint)
    
    # Track if parse_obj_as raises an exception
    parse_error = None
    try:
        result1 = parse_obj_as(type_hint, value)
    except Exception as e:
        parse_error = e
    
    # Track if TypeAdapter raises an exception
    adapter_error = None
    try:
        result2 = adapter.validate_python(value)
    except Exception as e:
        adapter_error = e
    
    # Check consistency
    if parse_error is None and adapter_error is None:
        # Both succeeded - results should match
        assert result1 == result2, f"Results differ for type {type_hint} with value {value}"
        assert type(result1) == type(result2), f"Types differ: {type(result1)} vs {type(result2)}"
    elif parse_error is not None and adapter_error is not None:
        # Both failed - that's consistent
        pass
    else:
        # One failed, one succeeded - inconsistent!
        assert False, f"Inconsistent behavior: parse_obj_as {'raised' if parse_error else 'succeeded'}, TypeAdapter {'raised' if adapter_error else 'succeeded'}"


# Property 3: schema_of with title parameter consistency
@given(
    type_hint=simple_type_annotations(),
    title=st.one_of(st.none(), st.text(min_size=1, max_size=50))
)
def test_schema_title_handling(type_hint, title):
    """Test that title parameter in schema_of is handled correctly."""
    if title is None:
        schema = schema_of(type_hint)
        # No title should be set if not provided
        # Actually we can't assert this since TypeAdapter might add one
    else:
        schema = schema_of(type_hint, title=title)
        # Title should be in the schema
        assert 'title' in schema
        assert schema['title'] == title


# Property 4: schema_json_of with dumps_kwargs
@given(
    type_hint=simple_type_annotations(),
    indent=st.integers(min_value=0, max_value=8)
)
def test_schema_json_formatting(type_hint, indent):
    """Test that schema_json_of respects dumps_kwargs."""
    schema_json = schema_json_of(type_hint, indent=indent)
    
    # Should be valid JSON
    parsed = json.loads(schema_json)
    
    # Re-dump with same indent to check formatting
    expected = json.dumps(parsed, indent=indent)
    assert schema_json == expected


# Property 5: Inverse property - valid parsed values should validate against their schemas
@given(
    type_hint=simple_type_annotations(),
    value=st.one_of(
        st.integers(min_value=-10000, max_value=10000),
        st.text(max_size=100),
        st.floats(allow_nan=False, allow_infinity=False, min_value=-1e6, max_value=1e6),
        st.booleans(),
        st.lists(st.integers(), max_size=5),
        st.dictionaries(st.text(max_size=20), st.integers(), max_size=5)
    )
)
@settings(max_examples=100)
def test_parsed_values_validate_against_schema(type_hint, value):
    """Test that values parsed by parse_obj_as are valid according to the schema."""
    try:
        # Parse the value
        parsed = parse_obj_as(type_hint, value)
        
        # Get the schema
        schema = schema_of(type_hint)
        
        # The parsed value should be serializable to JSON if the schema says so
        # This is a weak property but tests internal consistency
        if schema.get('type') in ['integer', 'string', 'number', 'boolean', 'array', 'object']:
            # Should be JSON serializable
            json.dumps(parsed, default=str)  # default=str to handle bytes
            
    except Exception:
        # If parsing fails, that's okay - not all values are valid
        pass


# Property 6: Type consistency - parse_obj_as preserves/coerces types correctly
@given(
    value=st.one_of(
        st.integers(),
        st.text(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.booleans(),
        st.lists(st.integers(), max_size=5)
    )
)
def test_parse_obj_as_type_coercion(value):
    """Test that parse_obj_as handles type coercion consistently."""
    # Test parsing to the actual type of the value
    if isinstance(value, bool):
        # bool is a subclass of int in Python, be careful
        result = parse_obj_as(bool, value)
        assert isinstance(result, bool)
        assert result == value
    elif isinstance(value, int):
        result = parse_obj_as(int, value)
        assert isinstance(result, int)
        assert result == value
    elif isinstance(value, str):
        result = parse_obj_as(str, value)
        assert isinstance(result, str)
        assert result == value
    elif isinstance(value, float):
        result = parse_obj_as(float, value)
        assert isinstance(result, float)
        assert result == value
    elif isinstance(value, list):
        result = parse_obj_as(list, value)
        assert isinstance(result, list)
        assert result == value