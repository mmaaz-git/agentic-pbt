"""Property-based tests for fire.value_types module."""

import math
import inspect
from hypothesis import assume, given, strategies as st
import pytest
import fire.value_types as vt


# Strategy for generating various Python objects
@st.composite
def python_objects(draw):
    """Generate various Python objects for testing classification."""
    choice = draw(st.integers(0, 10))
    
    if choice == 0:
        # Basic types (should be values)
        return draw(st.one_of(
            st.booleans(),
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.text(),
            st.binary(),
            st.complex_numbers(allow_nan=False, allow_infinity=False),
            st.none(),
            st.just(Ellipsis),
            st.just(NotImplemented)
        ))
    elif choice == 1:
        # Functions (should be commands)
        return lambda x: x
    elif choice == 2:
        # Classes (should be commands)
        class TestClass:
            pass
        return TestClass
    elif choice == 3:
        # Class instances with no custom __str__
        class NoStr:
            pass
        return NoStr()
    elif choice == 4:
        # Class instances with custom __str__
        class CustomStr:
            def __str__(self):
                return "custom"
        return CustomStr()
    elif choice == 5:
        # Built-in functions
        return max
    elif choice == 6:
        # Methods
        return "".join
    elif choice == 7:
        # Lists (should be groups)
        return draw(st.lists(st.integers()))
    elif choice == 8:
        # Dicts (should be groups)
        return draw(st.dictionaries(st.text(), st.integers()))
    elif choice == 9:
        # Tuples (should be groups)
        return draw(st.tuples(st.integers()))
    else:
        # Sets (should be groups)
        return draw(st.sets(st.integers()))


@given(python_objects())
def test_mutual_exclusivity(component):
    """A component should be classified as exactly one of: Command, Value, or Group."""
    is_command = vt.IsCommand(component)
    is_value = vt.IsValue(component)
    is_group = vt.IsGroup(component)
    
    # Count how many classifications are True
    classifications = sum([is_command, is_value, is_group])
    
    # Should be exactly one
    assert classifications == 1, (
        f"Component {component!r} has {classifications} classifications: "
        f"IsCommand={is_command}, IsValue={is_value}, IsGroup={is_group}"
    )


@given(st.sampled_from(vt.VALUE_TYPES))
def test_value_types_are_values(value_type):
    """All types in VALUE_TYPES should return True for IsValue when instantiated."""
    # Create an instance of the type
    if value_type == bool:
        instance = True
    elif value_type == str:
        instance = "test"
    elif value_type == bytes:
        instance = b"test"
    elif value_type == int:
        instance = 42
    elif value_type == float:
        instance = 3.14
    elif value_type == complex:
        instance = 1+2j
    elif value_type == type(Ellipsis):
        instance = Ellipsis
    elif value_type == type(None):
        instance = None
    elif value_type == type(NotImplemented):
        instance = NotImplemented
    else:
        pytest.skip(f"Unknown type {value_type}")
    
    assert vt.IsValue(instance), f"{instance!r} of type {value_type} should be a value"
    assert not vt.IsCommand(instance), f"{instance!r} should not be a command"
    assert not vt.IsGroup(instance), f"{instance!r} should not be a group"


@given(st.dictionaries(
    st.text(min_size=1),
    st.one_of(
        st.integers(),
        st.floats(allow_nan=False),
        st.text(),
        st.lists(st.integers()),
        st.dictionaries(st.text(), st.integers())
    ),
    min_size=0,
    max_size=10
))
def test_is_simple_group_with_values_only(component):
    """IsSimpleGroup should return True for dicts containing only values, lists, or dicts."""
    result = vt.IsSimpleGroup(component)
    
    # Check manually if all values are indeed values or lists/dicts
    all_simple = all(
        vt.IsValue(v) or isinstance(v, (list, dict))
        for v in component.values()
    )
    
    assert result == all_simple, (
        f"IsSimpleGroup returned {result} but manual check gives {all_simple} "
        f"for dict with values: {list(component.values())}"
    )


@given(python_objects())
def test_is_simple_group_requires_dict(component):
    """IsSimpleGroup should only accept dict inputs (has assert statement)."""
    if not isinstance(component, dict):
        with pytest.raises(AssertionError):
            vt.IsSimpleGroup(component)
    else:
        # Should not raise for dicts
        try:
            vt.IsSimpleGroup(component)
        except AssertionError:
            pytest.fail("IsSimpleGroup raised AssertionError for dict input")


def test_has_custom_str_on_primitives():
    """Primitives should have custom __str__ according to docstring."""
    assert vt.HasCustomStr(42), "int should have custom __str__"
    assert vt.HasCustomStr(3.14), "float should have custom __str__"
    assert vt.HasCustomStr("test"), "str should have custom __str__"
    assert vt.HasCustomStr(True), "bool should have custom __str__"


def test_has_custom_str_on_custom_class():
    """Classes with custom __str__ should be detected."""
    class WithCustomStr:
        def __str__(self):
            return "custom"
    
    class WithoutCustomStr:
        pass
    
    assert vt.HasCustomStr(WithCustomStr()), "Should detect custom __str__"
    assert not vt.HasCustomStr(WithoutCustomStr()), "Should not detect object's default __str__"


@given(st.one_of(
    st.just(lambda x: x),
    st.just(max),
    st.just(min),
    st.just(sorted),
    st.just(str.join)
))
def test_functions_are_commands(func):
    """Functions and methods should be classified as commands."""
    assert vt.IsCommand(func), f"{func} should be a command"
    assert not vt.IsValue(func), f"{func} should not be a value"
    assert not vt.IsGroup(func), f"{func} should not be a group"


def test_classes_are_commands():
    """Classes should be classified as commands."""
    class TestClass:
        pass
    
    assert vt.IsCommand(TestClass), "Class should be a command"
    assert not vt.IsValue(TestClass), "Class should not be a value"
    assert not vt.IsGroup(TestClass), "Class should not be a group"


@given(st.dictionaries(
    st.text(min_size=1),
    st.one_of(
        st.just(lambda x: x),  # function - not a value
        st.builds(type, st.just("TestClass"), st.tuples(), st.just({}))  # class - not a value
    ),
    min_size=1,
    max_size=5
))
def test_is_simple_group_with_non_values(component):
    """IsSimpleGroup should return False for dicts containing non-values (except lists/dicts)."""
    # This dict contains functions or classes, which are not values
    result = vt.IsSimpleGroup(component)
    assert result == False, (
        f"IsSimpleGroup should return False for dict with non-value items like functions/classes"
    )


# Test the relationship between IsGroup and the other functions
@given(python_objects())
def test_is_group_definition(component):
    """IsGroup should return True iff component is neither Command nor Value."""
    expected = not vt.IsCommand(component) and not vt.IsValue(component)
    actual = vt.IsGroup(component)
    assert actual == expected, (
        f"IsGroup returned {actual} but should be {expected} based on "
        f"IsCommand={vt.IsCommand(component)} and IsValue={vt.IsValue(component)}"
    )