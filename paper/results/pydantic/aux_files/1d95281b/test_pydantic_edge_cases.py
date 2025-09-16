"""Additional edge case tests for pydantic.dataclasses."""

import gc
import weakref
from typing import Optional, List, Dict, Any, ClassVar, Tuple
from hypothesis import given, strategies as st, assume, settings
from pydantic.dataclasses import dataclass, Field, rebuild_dataclass
from pydantic import ValidationError
import pytest


# Test circular references and memory leaks
@given(st.integers())
def test_circular_reference_memory(value):
    """Test that circular references don't cause memory leaks."""
    
    @dataclass
    class Node:
        value: int
        next: Optional['Node'] = None
    
    # Create circular reference
    node1 = Node(value=value)
    node2 = Node(value=value + 1, next=node1)
    node1.next = node2  # Create cycle
    
    # Create weak references to track garbage collection
    weak1 = weakref.ref(node1)
    weak2 = weakref.ref(node2)
    
    # Delete strong references
    del node1
    del node2
    
    # Force garbage collection
    gc.collect()
    
    # Check that objects were collected (no memory leak)
    assert weak1() is None, "Circular reference caused memory leak"
    assert weak2() is None, "Circular reference caused memory leak"


# Test ClassVar handling
@given(
    instance_var=st.integers(),
    class_var_value=st.integers()
)
def test_classvar_handling(instance_var, class_var_value):
    """Test that ClassVar fields are handled correctly."""
    
    @dataclass
    class WithClassVar:
        instance_field: int
        class_field: ClassVar[int] = class_var_value
    
    # ClassVar should not be part of instance initialization
    obj = WithClassVar(instance_field=instance_var)
    assert obj.instance_field == instance_var
    
    # ClassVar should be accessible as class attribute
    assert WithClassVar.class_field == class_var_value
    assert obj.class_field == class_var_value
    
    # Changing class var should affect all instances
    WithClassVar.class_field = class_var_value + 100
    assert obj.class_field == class_var_value + 100


# Test multiple inheritance with dataclasses
@given(
    base1_val=st.integers(),
    base2_val=st.text(max_size=10),
    derived_val=st.floats(allow_nan=False, allow_infinity=False)
)
def test_multiple_inheritance(base1_val, base2_val, derived_val):
    """Test multiple inheritance scenarios."""
    
    @dataclass
    class Base1:
        field1: int
    
    @dataclass
    class Base2:
        field2: str
    
    @dataclass
    class Derived(Base1, Base2):
        field3: float
    
    # Should be able to create with all fields
    obj = Derived(field1=base1_val, field2=base2_val, field3=derived_val)
    assert obj.field1 == base1_val
    assert obj.field2 == base2_val
    assert obj.field3 == derived_val


# Test with very long field names
@given(
    field_suffix=st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=50, max_size=100),
    value=st.integers()
)
def test_long_field_names(field_suffix, value):
    """Test dataclasses with very long field names."""
    field_name = f"field_{field_suffix}"
    
    cls = type('LongFieldTest', (), {
        '__annotations__': {field_name: int},
        field_name: 0
    })
    
    DataClass = dataclass(cls)
    obj = DataClass(**{field_name: value})
    assert getattr(obj, field_name) == value


# Test order parameter with custom comparison
@given(
    values=st.lists(st.integers(), min_size=2, max_size=10)
)
def test_order_parameter(values):
    """Test that order=True enables comparison operators."""
    assume(len(set(values)) > 1)  # Need different values
    
    @dataclass(order=True)
    class Ordered:
        value: int
    
    # Create instances
    instances = [Ordered(value=v) for v in values]
    
    # Sort should work
    sorted_instances = sorted(instances)
    sorted_values = [inst.value for inst in sorted_instances]
    assert sorted_values == sorted(values)
    
    # Comparison operators should work
    if len(values) >= 2 and values[0] != values[1]:
        obj1 = Ordered(value=min(values[0], values[1]))
        obj2 = Ordered(value=max(values[0], values[1]))
        assert obj1 < obj2
        assert obj2 > obj1
        assert obj1 <= obj2
        assert obj2 >= obj1


# Test with properties and descriptors
@given(
    initial_value=st.integers(),
    multiplier=st.integers(min_value=1, max_value=10)
)
def test_with_properties(initial_value, multiplier):
    """Test dataclasses with properties and computed fields."""
    
    @dataclass
    class WithProperty:
        _value: int = Field(alias='value')
        
        @property
        def computed(self) -> int:
            return self._value * multiplier
    
    obj = WithProperty(value=initial_value)
    assert obj._value == initial_value
    assert obj.computed == initial_value * multiplier


# Test field constraints with edge values
@given(st.data())
def test_field_constraints_edge_cases(data):
    """Test field constraints with edge values."""
    
    @dataclass
    class Constrained:
        positive: int = Field(gt=0)
        bounded: int = Field(ge=-100, le=100)
        non_empty: str = Field(min_length=1)
        limited_str: str = Field(max_length=10)
    
    # Test valid values
    obj = Constrained(
        positive=data.draw(st.integers(min_value=1, max_value=1000)),
        bounded=data.draw(st.integers(min_value=-100, max_value=100)),
        non_empty=data.draw(st.text(min_size=1, max_size=100)),
        limited_str=data.draw(st.text(min_size=0, max_size=10))
    )
    
    # Test boundary violations
    with pytest.raises(ValidationError):
        Constrained(positive=0, bounded=0, non_empty="a", limited_str="")
    
    with pytest.raises(ValidationError):
        Constrained(positive=1, bounded=101, non_empty="a", limited_str="a")
    
    with pytest.raises(ValidationError):
        Constrained(positive=1, bounded=0, non_empty="", limited_str="a")
    
    with pytest.raises(ValidationError):
        Constrained(positive=1, bounded=0, non_empty="a", limited_str="a" * 11)


# Test __post_init__ hook
@given(
    initial_value=st.integers()
)
def test_post_init_hook(initial_value):
    """Test that __post_init__ is called correctly."""
    post_init_called = []
    
    @dataclass
    class WithPostInit:
        value: int
        computed: Optional[int] = None
        
        def __post_init__(self):
            post_init_called.append(True)
            if self.computed is None:
                self.computed = self.value * 2
    
    obj = WithPostInit(value=initial_value)
    assert len(post_init_called) == 1, "__post_init__ not called"
    assert obj.computed == initial_value * 2, "__post_init__ didn't set computed field"


# Test with complex nested structures
@given(
    st.lists(
        st.tuples(
            st.integers(),
            st.text(max_size=10),
            st.lists(st.integers(), max_size=5)
        ),
        min_size=1,
        max_size=5
    )
)
def test_complex_nested_structures(data_list):
    """Test complex nested dataclass structures."""
    
    @dataclass
    class Inner:
        items: List[int]
    
    @dataclass
    class Middle:
        name: str
        inner: Inner
    
    @dataclass
    class Outer:
        id: int
        middle: Middle
    
    # Create nested structure
    for id_val, name, items in data_list:
        inner = Inner(items=items)
        middle = Middle(name=name, inner=inner)
        outer = Outer(id=id_val, middle=middle)
        
        # Verify structure
        assert outer.id == id_val
        assert outer.middle.name == name
        assert outer.middle.inner.items == items


# Test dataclass with __slots__
@given(
    value=st.integers()
)  
def test_slots_with_inheritance(value):
    """Test slots with inheritance scenarios."""
    
    @dataclass(slots=True)
    class SlottedBase:
        base_field: int
    
    @dataclass(slots=True)
    class SlottedDerived(SlottedBase):
        derived_field: int
    
    obj = SlottedDerived(base_field=value, derived_field=value + 1)
    assert obj.base_field == value
    assert obj.derived_field == value + 1
    
    # Should not be able to add new attributes
    with pytest.raises(AttributeError):
        obj.new_attr = 123