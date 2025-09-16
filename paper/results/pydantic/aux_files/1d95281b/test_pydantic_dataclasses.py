"""Property-based tests for pydantic.dataclasses module."""

import string
from typing import Optional, List, Dict, Any, ForwardRef
from dataclasses import is_dataclass
from hypothesis import given, strategies as st, assume, settings
from hypothesis.strategies import composite
from pydantic.dataclasses import dataclass, is_pydantic_dataclass, rebuild_dataclass, Field
from pydantic import ValidationError
import pytest


# Strategy for generating valid Python identifiers
@composite
def python_identifier(draw):
    """Generate valid Python identifiers."""
    first_char = draw(st.sampled_from(string.ascii_letters + '_'))
    rest = draw(st.text(alphabet=string.ascii_letters + string.digits + '_', min_size=0, max_size=10))
    return first_char + rest


# Strategy for generating simple type annotations
@composite
def simple_type_annotation(draw):
    """Generate simple type annotations."""
    return draw(st.sampled_from([
        'int', 'str', 'float', 'bool',
        'Optional[int]', 'Optional[str]',
        'List[int]', 'List[str]',
        'Dict[str, int]'
    ]))


# Test 1: is_pydantic_dataclass invariant
@given(
    class_name=python_identifier(),
    field_names=st.lists(python_identifier(), min_size=1, max_size=5, unique=True),
    frozen=st.booleans(),
    eq=st.booleans(),
    repr=st.booleans()
)
def test_is_pydantic_dataclass_invariant(class_name, field_names, frozen, eq, repr):
    """Test that is_pydantic_dataclass returns True for all pydantic dataclasses."""
    # Dynamically create a class
    class_dict = {}
    for field_name in field_names:
        class_dict[field_name] = int
    
    # Create the class dynamically
    cls = type(class_name, (), {
        '__annotations__': class_dict,
        **{name: 0 for name in field_names}  # Default values
    })
    
    # Apply the dataclass decorator
    decorated_cls = dataclass(cls, frozen=frozen, eq=eq, repr=repr)
    
    # Property: is_pydantic_dataclass should return True
    assert is_pydantic_dataclass(decorated_cls), \
        f"is_pydantic_dataclass returned False for a pydantic dataclass"
    
    # Additional check: should also be a standard dataclass
    assert is_dataclass(decorated_cls), \
        "Pydantic dataclass is not recognized as a standard dataclass"


# Test 2: Equality property
@given(
    field_values=st.dictionaries(
        keys=python_identifier(),
        values=st.one_of(
            st.integers(),
            st.text(max_size=50),
            st.floats(allow_nan=False, allow_infinity=False),
            st.booleans()
        ),
        min_size=1,
        max_size=5
    )
)
def test_equality_property(field_values):
    """Test that instances with same values are equal when eq=True."""
    # Create a dataclass with the given fields
    annotations = {name: type(value).__name__ for name, value in field_values.items()}
    
    cls = type('EqualityTest', (), {
        '__annotations__': annotations,
        **{name: None for name in field_values}
    })
    
    # Create dataclass with eq=True
    EqClass = dataclass(cls, eq=True)
    
    # Create two instances with same values
    instance1 = EqClass(**field_values)
    instance2 = EqClass(**field_values)
    
    # Property: instances with same values should be equal
    assert instance1 == instance2, "Instances with same values are not equal"
    
    # Note: dataclasses with eq=True are not hashable by default (same as standard dataclasses)
    # Only check hash if the class is actually hashable
    try:
        h1 = hash(instance1)
        h2 = hash(instance2)
        assert h1 == h2, "Instances with same values have different hashes"
    except TypeError:
        # Expected - dataclasses with eq=True are not hashable by default
        pass
    
    # They should not be the same object
    assert instance1 is not instance2, "Instances should be different objects"


# Test 3: Frozen immutability
@given(
    initial_value=st.integers(),
    new_value=st.integers(),
    field_name=python_identifier()
)
def test_frozen_immutability(initial_value, new_value, field_name):
    """Test that frozen dataclasses are truly immutable."""
    assume(initial_value != new_value)
    
    # Create a frozen dataclass
    cls = type('FrozenTest', (), {
        '__annotations__': {field_name: int},
        field_name: initial_value
    })
    
    FrozenClass = dataclass(cls, frozen=True)
    instance = FrozenClass(**{field_name: initial_value})
    
    # Property: should not be able to modify frozen instance
    with pytest.raises(Exception):  # Could be FrozenInstanceError or AttributeError
        setattr(instance, field_name, new_value)
    
    # Value should remain unchanged
    assert getattr(instance, field_name) == initial_value


# Test 4: rebuild_dataclass idempotence
@given(
    class_name=python_identifier(),
    has_forward_ref=st.booleans()
)
def test_rebuild_dataclass_idempotence(class_name, has_forward_ref):
    """Test that rebuild_dataclass is idempotent."""
    # Create a dataclass, potentially with forward reference
    if has_forward_ref:
        cls = type(class_name, (), {
            '__annotations__': {
                'value': int,
                'self_ref': f'Optional["{class_name}"]'
            },
            'value': 0,
            'self_ref': None
        })
    else:
        cls = type(class_name, (), {
            '__annotations__': {'value': int},
            'value': 0
        })
    
    decorated_cls = dataclass(cls)
    
    # Call rebuild_dataclass multiple times
    result1 = rebuild_dataclass(decorated_cls, force=True)
    result2 = rebuild_dataclass(decorated_cls, force=True)
    result3 = rebuild_dataclass(decorated_cls, force=True)
    
    # Property: multiple rebuilds should give consistent results
    assert result1 == result2 == result3, \
        "rebuild_dataclass is not idempotent"
    
    # The class should still be usable
    instance = decorated_cls(value=42)
    assert instance.value == 42


# Test 5: Field default_factory isolation
@given(
    num_instances=st.integers(min_value=2, max_value=10)
)
def test_default_factory_isolation(num_instances):
    """Test that default_factory creates new instances each time."""
    # Create a dataclass with a mutable default using default_factory
    @dataclass
    class FactoryTest:
        items: List[int] = Field(default_factory=list)
        data: Dict[str, int] = Field(default_factory=dict)
    
    # Create multiple instances
    instances = [FactoryTest() for _ in range(num_instances)]
    
    # Modify the first instance's mutable fields
    instances[0].items.append(42)
    instances[0].data['key'] = 100
    
    # Property: other instances should not be affected
    for i in range(1, num_instances):
        assert instances[i].items == [], \
            f"Instance {i} list was modified when instance 0 was changed"
        assert instances[i].data == {}, \
            f"Instance {i} dict was modified when instance 0 was changed"
    
    # All instances should have different list/dict objects
    for i in range(num_instances):
        for j in range(i + 1, num_instances):
            assert instances[i].items is not instances[j].items, \
                f"Instances {i} and {j} share the same list object"
            assert instances[i].data is not instances[j].data, \
                f"Instances {i} and {j} share the same dict object"


# Test 6: Nested dataclass validation
@given(
    outer_value=st.integers(),
    inner_value=st.integers(min_value=0, max_value=100)
)
def test_nested_dataclass_validation(outer_value, inner_value):
    """Test that nested dataclasses validate correctly."""
    @dataclass
    class Inner:
        value: int = Field(ge=0, le=100)  # Must be between 0 and 100
    
    @dataclass
    class Outer:
        inner: Inner
        outer_value: int
    
    # Valid nested structure should work
    inner_obj = Inner(value=inner_value)
    outer_obj = Outer(inner=inner_obj, outer_value=outer_value)
    
    assert outer_obj.inner.value == inner_value
    assert outer_obj.outer_value == outer_value
    
    # Invalid inner value should raise ValidationError
    with pytest.raises(ValidationError):
        Inner(value=-1)
    
    with pytest.raises(ValidationError):
        Inner(value=101)


# Test 7: Complex inheritance scenarios
@given(
    base_value=st.integers(),
    derived_value=st.text(max_size=20)
)
def test_inheritance_chain(base_value, derived_value):
    """Test that inheritance works correctly with pydantic dataclasses."""
    @dataclass
    class Base:
        base_field: int
    
    @dataclass
    class Derived(Base):
        derived_field: str
    
    # Create instance of derived class
    obj = Derived(base_field=base_value, derived_field=derived_value)
    
    # Properties: fields from both base and derived should work
    assert obj.base_field == base_value
    assert obj.derived_field == derived_value
    
    # Should be instance of both classes
    assert isinstance(obj, Derived)
    assert isinstance(obj, Base)
    
    # Both should be pydantic dataclasses
    assert is_pydantic_dataclass(Base)
    assert is_pydantic_dataclass(Derived)


# Test 8: repr consistency
@given(
    values=st.dictionaries(
        keys=st.sampled_from(['a', 'b', 'c']),
        values=st.one_of(st.integers(), st.text(max_size=10)),
        min_size=1,
        max_size=3
    )
)
def test_repr_consistency(values):
    """Test that repr is consistent and can be evaluated."""
    # Create a dataclass
    annotations = {k: type(v).__name__ for k, v in values.items()}
    cls = type('ReprTest', (), {
        '__annotations__': annotations,
        **{k: None for k in values}
    })
    
    ReprClass = dataclass(cls, repr=True)
    instance = ReprClass(**values)
    
    # Get the repr
    repr_str = repr(instance)
    
    # Property: repr should contain class name and all field values
    assert 'ReprTest' in repr_str
    for key, value in values.items():
        assert key in repr_str
        # Value should be represented somehow (exact format may vary)
    
    # Creating another instance with same values should give same repr
    instance2 = ReprClass(**values)
    assert repr(instance) == repr(instance2)


# Test 9: slots behavior
@given(
    use_slots=st.booleans(),
    field_name=python_identifier(),
    value=st.integers()
)
def test_slots_behavior(use_slots, field_name, value):
    """Test that slots parameter works correctly."""
    # Create dataclass with or without slots
    cls = type('SlotsTest', (), {
        '__annotations__': {field_name: int},
        field_name: 0
    })
    
    SlotsClass = dataclass(cls, slots=use_slots)
    instance = SlotsClass(**{field_name: value})
    
    # Check if slots is actually used
    if use_slots:
        # With slots, the class should have __slots__
        assert hasattr(SlotsClass, '__slots__'), "slots=True but no __slots__ found"
        # Should not be able to add arbitrary attributes
        with pytest.raises(AttributeError):
            instance.arbitrary_new_attribute = 123
    else:
        # Without slots, should be able to add attributes
        instance.arbitrary_new_attribute = 123
        assert instance.arbitrary_new_attribute == 123


# Test 10: kw_only parameter
@given(
    kw_only=st.booleans(),
    value1=st.integers(),
    value2=st.text(max_size=10)
)
def test_kw_only_parameter(kw_only, value1, value2):
    """Test that kw_only parameter affects initialization."""
    @dataclass(kw_only=kw_only)
    class KwOnlyTest:
        field1: int
        field2: str
    
    # With kw_only=True, should only accept keyword arguments
    if kw_only:
        # This should work with keywords
        instance = KwOnlyTest(field1=value1, field2=value2)
        assert instance.field1 == value1
        assert instance.field2 == value2
        
        # Positional should fail (with ValidationError, not TypeError)
        with pytest.raises(ValidationError):
            KwOnlyTest(value1, value2)
    else:
        # Should work both ways
        instance1 = KwOnlyTest(value1, value2)
        instance2 = KwOnlyTest(field1=value1, field2=value2)
        assert instance1.field1 == instance2.field1 == value1
        assert instance1.field2 == instance2.field2 == value2