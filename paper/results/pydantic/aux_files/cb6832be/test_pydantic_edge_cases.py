import json
import math
from typing import Optional, List, Dict, Any, Union
from decimal import Decimal
from datetime import datetime, date, time
from enum import Enum

import pytest
from hypothesis import given, strategies as st, settings, assume, note
import pydantic
from pydantic import BaseModel, Field, ValidationError


# Test for edge cases in JSON serialization
@given(
    special_float=st.sampled_from([
        float('inf'), 
        float('-inf'), 
        float('nan'),
        0.0,
        -0.0,
        1e308,  # Near max float
        1e-308,  # Near min positive float
    ])
)
def test_special_float_json_serialization(special_float):
    """Test that special float values are handled correctly in JSON"""
    
    class Model(BaseModel):
        value: float
    
    m = Model(value=special_float)
    
    # Check if JSON serialization handles special values
    try:
        json_str = m.model_dump_json()
        # If it serializes, can we deserialize?
        if not math.isnan(special_float):
            m2 = Model.model_validate_json(json_str)
            if math.isinf(special_float):
                assert math.isinf(m2.value)
                assert (special_float > 0) == (m2.value > 0)  # Same sign
            else:
                assert m.value == m2.value or (m.value == 0.0 and m2.value == 0.0)
    except (ValueError, ValidationError) as e:
        # Some special values might not be JSON serializable
        note(f"Failed to serialize/deserialize {special_float}: {e}")


# Test Unicode edge cases
@given(
    text=st.text(
        alphabet=st.one_of(
            st.sampled_from([
                '\x00',  # Null character
                '\u200b',  # Zero-width space
                '\ufeff',  # Zero-width no-break space (BOM)
                '\U0001f4a9',  # Emoji
                '\u0301',  # Combining character
                '𐐷',  # 4-byte UTF-8 character
            ]),
            st.characters(min_codepoint=0x10000, max_codepoint=0x10ffff)  # Astral plane
        ),
        min_size=1,
        max_size=10
    )
)
def test_unicode_edge_cases(text):
    """Test that unusual Unicode characters are preserved"""
    
    class Model(BaseModel):
        text: str
    
    m = Model(text=text)
    
    # Test JSON round-trip
    json_str = m.model_dump_json()
    m2 = Model.model_validate_json(json_str)
    assert m.text == m2.text
    
    # Test dict round-trip
    d = m.model_dump()
    m3 = Model.model_validate(d)
    assert m.text == m3.text


# Test datetime edge cases
@given(
    year=st.integers(min_value=1, max_value=9999),
    month=st.integers(min_value=1, max_value=12),
    day=st.integers(min_value=1, max_value=28),  # Safe for all months
    hour=st.integers(min_value=0, max_value=23),
    minute=st.integers(min_value=0, max_value=59),
    second=st.integers(min_value=0, max_value=59),
    microsecond=st.integers(min_value=0, max_value=999999)
)
def test_datetime_roundtrip(year, month, day, hour, minute, second, microsecond):
    """Test datetime serialization round-trip"""
    
    class Model(BaseModel):
        dt: datetime
    
    dt = datetime(year, month, day, hour, minute, second, microsecond)
    m = Model(dt=dt)
    
    # JSON round-trip
    json_str = m.model_dump_json()
    m2 = Model.model_validate_json(json_str)
    assert m.dt == m2.dt


# Test enum handling
class Color(Enum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"

@given(
    color=st.sampled_from(list(Color))
)
def test_enum_json_roundtrip(color):
    """Test that enums serialize and deserialize correctly"""
    
    class Model(BaseModel):
        color: Color
    
    m = Model(color=color)
    
    # JSON round-trip
    json_str = m.model_dump_json()
    m2 = Model.model_validate_json(json_str)
    assert m.color == m2.color
    assert isinstance(m2.color, Color)


# Test mutually recursive models
def test_recursive_model_json_roundtrip():
    """Test that mutually recursive models handle JSON correctly"""
    
    class Node(BaseModel):
        value: int
        children: List['Node'] = []
    
    # Create a tree structure
    root = Node(
        value=1,
        children=[
            Node(value=2, children=[Node(value=4), Node(value=5)]),
            Node(value=3)
        ]
    )
    
    # JSON round-trip
    json_str = root.model_dump_json()
    root2 = Node.model_validate_json(json_str)
    
    assert root.value == root2.value
    assert len(root.children) == len(root2.children)
    assert root.children[0].value == root2.children[0].value
    assert len(root.children[0].children) == len(root2.children[0].children)


# Test discriminated unions
@given(
    kind=st.sampled_from(['circle', 'square']),
    size=st.floats(min_value=0.1, max_value=100, allow_nan=False)
)
def test_discriminated_union_roundtrip(kind, size):
    """Test discriminated union serialization"""
    
    class Circle(BaseModel):
        kind: str = Field('circle', frozen=True)
        radius: float
    
    class Square(BaseModel):
        kind: str = Field('square', frozen=True)
        side: float
    
    class Drawing(BaseModel):
        shape: Union[Circle, Square] = Field(discriminator='kind')
    
    if kind == 'circle':
        shape = Circle(radius=size)
    else:
        shape = Square(side=size)
    
    drawing = Drawing(shape=shape)
    
    # JSON round-trip
    json_str = drawing.model_dump_json()
    drawing2 = Drawing.model_validate_json(json_str)
    
    assert drawing.shape.kind == drawing2.shape.kind
    if kind == 'circle':
        assert drawing.shape.radius == drawing2.shape.radius
    else:
        assert drawing.shape.side == drawing2.shape.side


# Test deeply nested structures
@given(
    depth=st.integers(min_value=10, max_value=100)
)
def test_deeply_nested_lists(depth):
    """Test deeply nested list structures"""
    
    class Model(BaseModel):
        data: Any
    
    # Create deeply nested list
    nested = 42
    for _ in range(depth):
        nested = [nested]
    
    m = Model(data=nested)
    
    # JSON round-trip
    json_str = m.model_dump_json()
    m2 = Model.model_validate_json(json_str)
    
    # Verify depth is preserved
    current = m2.data
    for _ in range(depth):
        assert isinstance(current, list)
        assert len(current) == 1
        current = current[0]
    assert current == 42


# Test field ordering preservation
@given(
    keys=st.lists(
        st.text(alphabet=st.characters(blacklist_categories=('Cc', 'Cs')), min_size=1, max_size=10),
        min_size=2,
        max_size=5,
        unique=True
    )
)
def test_dict_field_order_preservation(keys):
    """Test that dict field order is preserved in recent Python versions"""
    
    class Model(BaseModel):
        data: Dict[str, int]
    
    # Create ordered dict
    data = {k: i for i, k in enumerate(keys)}
    m = Model(data=data)
    
    # Check if order is preserved in model_dump
    dumped = m.model_dump()
    assert list(dumped['data'].keys()) == keys
    
    # JSON round-trip
    json_str = m.model_dump_json()
    m2 = Model.model_validate_json(json_str)
    
    # In Python 3.7+, dict order should be preserved
    assert list(m2.data.keys()) == keys


# Test bytes handling
@given(
    data=st.binary(min_size=0, max_size=100)
)
def test_bytes_json_serialization(data):
    """Test bytes field JSON serialization"""
    
    class Model(BaseModel):
        data: bytes
    
    m = Model(data=data)
    
    # JSON round-trip
    json_str = m.model_dump_json()
    m2 = Model.model_validate_json(json_str)
    
    assert m.data == m2.data


# Test model_dump with include/exclude
@given(
    include_a=st.booleans(),
    include_b=st.booleans(),
    include_c=st.booleans()
)
def test_model_dump_include_exclude(include_a, include_b, include_c):
    """Test model_dump with include/exclude parameters"""
    
    class Model(BaseModel):
        a: int = 1
        b: int = 2
        c: int = 3
    
    m = Model()
    
    # Build include set
    include = set()
    if include_a:
        include.add('a')
    if include_b:
        include.add('b')
    if include_c:
        include.add('c')
    
    if include:
        dumped = m.model_dump(include=include)
        assert set(dumped.keys()) == include
        
        # Round-trip with partial data should fail or use defaults
        if len(include) < 3:
            # Should use defaults for missing fields
            m2 = Model.model_validate(dumped)
            for field in ['a', 'b', 'c']:
                if field in include:
                    assert getattr(m2, field) == getattr(m, field)


if __name__ == "__main__":
    print("Running edge case tests...")
    test_special_float_json_serialization(float('inf'))
    test_recursive_model_json_roundtrip()
    print("Basic tests passed!")