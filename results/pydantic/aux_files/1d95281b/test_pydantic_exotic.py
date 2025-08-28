"""Exotic edge case tests for pydantic.dataclasses to find potential bugs."""

from typing import Optional, List, Dict, Any, Union, Literal, TypeVar, Generic
from hypothesis import given, strategies as st, assume, settings, note
from pydantic.dataclasses import dataclass, Field
from pydantic import ValidationError
import pytest
import sys


# Test with empty dataclass
@given(st.integers())
def test_empty_dataclass(value):
    """Test dataclass with no fields."""
    
    @dataclass
    class Empty:
        pass
    
    # Should be able to create instances
    obj1 = Empty()
    obj2 = Empty()
    
    # Instances should be equal since no fields
    assert obj1 == obj2
    
    # Should be able to add attributes dynamically (unless slots is used)
    obj1.dynamic = value
    assert obj1.dynamic == value


# Test with Union types
@given(
    int_or_str=st.one_of(st.integers(), st.text(max_size=10))
)
def test_union_types(int_or_str):
    """Test dataclasses with Union type annotations."""
    
    @dataclass
    class WithUnion:
        value: Union[int, str]
        optional_union: Optional[Union[int, str]] = None
    
    obj = WithUnion(value=int_or_str)
    assert obj.value == int_or_str
    
    # Test with the optional field
    obj2 = WithUnion(value=int_or_str, optional_union=int_or_str)
    assert obj2.optional_union == int_or_str


# Test with Literal types
@given(
    literal_choice=st.sampled_from(['option1', 'option2', 'option3'])
)
def test_literal_types(literal_choice):
    """Test dataclasses with Literal type annotations."""
    
    @dataclass
    class WithLiteral:
        choice: Literal['option1', 'option2', 'option3']
    
    # Valid literal should work
    obj = WithLiteral(choice=literal_choice)
    assert obj.choice == literal_choice
    
    # Invalid literal should fail
    with pytest.raises(ValidationError):
        WithLiteral(choice='invalid_option')


# Test with Generic types
T = TypeVar('T')

@given(
    value=st.one_of(st.integers(), st.text(max_size=10), st.floats(allow_nan=False))
)
def test_generic_dataclass(value):
    """Test generic dataclasses."""
    
    @dataclass
    class Container(Generic[T]):
        item: T
        items: List[T] = Field(default_factory=list)
    
    # Create container with specific type
    container = Container(item=value)
    assert container.item == value
    
    # Add items of same type
    container.items.append(value)
    assert container.items == [value]


# Test field name conflicts
@given(st.integers())
def test_field_name_conflicts(value):
    """Test dataclasses with potentially conflicting field names."""
    
    # Test with Python keywords (should work with aliases)
    @dataclass
    class WithKeywords:
        class_: int = Field(alias='class')
        type_: int = Field(alias='type')
    
    obj = WithKeywords(**{'class': value, 'type': value + 1})
    assert obj.class_ == value
    assert obj.type_ == value + 1


# Test with very large number of fields
@given(st.integers(min_value=0, max_value=100))
def test_many_fields(base_value):
    """Test dataclass with many fields."""
    # Create class with 50 fields
    num_fields = 50
    annotations = {f'field_{i}': int for i in range(num_fields)}
    defaults = {f'field_{i}': i for i in range(num_fields)}
    
    cls = type('ManyFields', (), {
        '__annotations__': annotations,
        **defaults
    })
    
    ManyFieldsClass = dataclass(cls)
    
    # Create with all defaults
    obj1 = ManyFieldsClass()
    for i in range(num_fields):
        assert getattr(obj1, f'field_{i}') == i
    
    # Create with custom values
    custom_values = {f'field_{i}': base_value + i for i in range(num_fields)}
    obj2 = ManyFieldsClass(**custom_values)
    for i in range(num_fields):
        assert getattr(obj2, f'field_{i}') == base_value + i


# Test recursive validation
@given(
    depth=st.integers(min_value=1, max_value=5),
    value=st.integers()
)
def test_recursive_validation(depth, value):
    """Test deeply nested structures with validation."""
    
    @dataclass
    class RecursiveNode:
        value: int = Field(ge=0)  # Must be non-negative
        child: Optional['RecursiveNode'] = None
    
    # Build nested structure (ensure values are non-negative)
    node = None
    for i in range(depth):
        node = RecursiveNode(value=abs(value) + i, child=node)
    
    # Count depth
    current = node
    count = 0
    while current:
        count += 1
        current = current.child
    assert count == depth
    
    # Validation should work at all levels
    with pytest.raises(ValidationError):
        RecursiveNode(value=-1)  # Invalid at top level
    
    # Invalid nested value should also fail
    with pytest.raises(ValidationError):
        RecursiveNode(value=1, child=RecursiveNode(value=-1))


# Test with callable defaults
@given(st.integers())
def test_callable_defaults(value):
    """Test fields with callable defaults."""
    counter = [0]
    
    def increment_counter():
        counter[0] += 1
        return counter[0]
    
    @dataclass
    class WithCallableDefault:
        value: int
        auto_id: int = Field(default_factory=increment_counter)
    
    # Each instance should get a unique auto_id
    obj1 = WithCallableDefault(value=value)
    obj2 = WithCallableDefault(value=value)
    obj3 = WithCallableDefault(value=value)
    
    assert obj1.auto_id == 1
    assert obj2.auto_id == 2
    assert obj3.auto_id == 3


# Test init=False parameter
def test_init_false_parameter():
    """Test that init=False is handled correctly."""
    
    @dataclass(init=False)
    class NoInit:
        value: int = 10
    
    # Should still have __init__ (pydantic always generates it)
    assert hasattr(NoInit, '__init__')
    
    # But it should work differently
    obj = NoInit()
    assert obj.value == 10


# Test with bytes
@given(
    data=st.binary(min_size=0, max_size=100)
)
def test_bytes_fields(data):
    """Test dataclasses with bytes fields."""
    
    @dataclass
    class BytesData:
        raw_bytes: bytes
        optional_bytes: Optional[bytes] = None
    
    obj = BytesData(raw_bytes=data)
    assert obj.raw_bytes == data
    assert isinstance(obj.raw_bytes, bytes)
    
    obj2 = BytesData(raw_bytes=data, optional_bytes=b'test')
    assert obj2.optional_bytes == b'test'


# Test dataclass with __new__ override
@given(st.integers())
def test_with_custom_new(value):
    """Test dataclass with custom __new__ method."""
    
    @dataclass
    class WithCustomNew:
        value: int
        
        def __new__(cls, **kwargs):
            # Custom instantiation logic
            instance = object.__new__(cls)
            # Could do custom stuff here
            return instance
    
    obj = WithCustomNew(value=value)
    assert obj.value == value


# Test with complex default values
@given(st.integers())
def test_mutable_defaults_safety(value):
    """Test that mutable defaults are handled safely."""
    
    @dataclass
    class UnsafeLooking:
        # This would be unsafe in regular Python but pydantic handles it
        items: List[int] = Field(default_factory=lambda: [1, 2, 3])
        mapping: Dict[str, int] = Field(default_factory=lambda: {'a': 1})
    
    obj1 = UnsafeLooking()
    obj2 = UnsafeLooking()
    
    # Modify obj1
    obj1.items.append(value)
    obj1.mapping['b'] = value
    
    # obj2 should not be affected
    assert obj2.items == [1, 2, 3]
    assert obj2.mapping == {'a': 1}
    
    # They should have different objects
    assert obj1.items is not obj2.items
    assert obj1.mapping is not obj2.mapping