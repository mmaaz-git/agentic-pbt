import functools
import random
from typing import Any, Type

from hypothesis import assume, given, strategies as st
from hypothesis.strategies import SearchStrategy


def create_test_types(num_types: int = 5) -> list[Type]:
    """Create a list of dynamically generated types for testing."""
    types = []
    for i in range(num_types):
        class_name = f"TestClass{i}"
        types.append(type(class_name, (object,), {}))
    return types


def create_inheritance_chain(depth: int = 3) -> list[Type]:
    """Create a chain of classes with inheritance."""
    chain = []
    base = type("Base", (object,), {})
    chain.append(base)
    
    for i in range(1, depth):
        parent = chain[-1]
        child = type(f"Child{i}", (parent,), {})
        chain.append(child)
    
    return chain


@st.composite
def type_and_value(draw: st.DrawFn) -> tuple[Type, Any]:
    """Generate a type and a corresponding value of that type."""
    type_choice = draw(st.integers(0, 4))
    
    if type_choice == 0:
        return int, draw(st.integers())
    elif type_choice == 1:
        return str, draw(st.text())
    elif type_choice == 2:
        return list, draw(st.lists(st.integers(), max_size=10))
    elif type_choice == 3:
        return dict, draw(st.dictionaries(st.text(max_size=5), st.integers(), max_size=5))
    else:
        return float, draw(st.floats(allow_nan=False, allow_infinity=False))


@given(
    st.lists(
        st.sampled_from([int, str, list, dict, float, tuple, set, frozenset, bytes]),
        min_size=1,
        max_size=8,
        unique=True
    )
)
def test_dispatch_registry_consistency(types_to_register):
    """Test that dispatch(T) always returns the same handler as registry[T]."""
    
    @functools.singledispatch
    def test_func(arg):
        return "default"
    
    # Register handlers for each type
    handlers = {}
    for typ in types_to_register:
        def make_handler(t):
            def handler(arg):
                return f"handler_for_{t.__name__}"
            return handler
        
        handler = make_handler(typ)
        test_func.register(typ, handler)
        handlers[typ] = handler
    
    # Property: dispatch(T) should return the same function as registry[T]
    for typ in types_to_register:
        dispatched = test_func.dispatch(typ)
        registered = test_func.registry.get(typ)
        
        if registered is not None:
            assert dispatched is registered, f"Mismatch for {typ}: dispatch returned {dispatched}, registry has {registered}"


@given(
    st.sampled_from([int, str, list, dict, float]),
    st.integers(2, 10)
)
def test_reregistration_overwrites(target_type, num_registrations):
    """Test that re-registering for the same type overwrites the previous handler."""
    
    @functools.singledispatch
    def test_func(arg):
        return "default"
    
    handlers = []
    
    # Register multiple handlers for the same type
    for i in range(num_registrations):
        def make_handler(index):
            def handler(arg):
                return f"handler_{index}"
            return handler
        
        handler = make_handler(i)
        test_func.register(target_type, handler)
        handlers.append(handler)
    
    # Property: The last registered handler should be the active one
    final_handler = test_func.dispatch(target_type)
    last_registered = handlers[-1]
    
    # The final handler should be the last one we registered
    test_value = target_type() if target_type != dict else {}
    result = test_func(test_value)
    expected = f"handler_{num_registrations - 1}"
    
    assert result == expected, f"Expected {expected}, got {result}"


@given(st.integers(2, 5))
def test_inheritance_resolution(chain_length):
    """Test that subclasses use parent handlers when not specifically registered."""
    assume(chain_length >= 2)
    
    # Create inheritance chain
    chain = create_inheritance_chain(chain_length)
    
    @functools.singledispatch
    def test_func(arg):
        return "default"
    
    # Register handler only for the base class
    @test_func.register(chain[0])
    def base_handler(arg):
        return "base_handler"
    
    # Property: All subclasses should use the base handler
    for i, cls in enumerate(chain):
        instance = cls()
        result = test_func(instance)
        
        # The first class has a registered handler, all should use it
        assert result == "base_handler", f"Class at position {i} returned {result}"
        
        # Also test dispatch directly
        handler = test_func.dispatch(cls)
        assert handler is base_handler, f"Dispatch for class at position {i} returned wrong handler"


@given(st.integers(2, 5))
def test_inheritance_with_override(chain_length):
    """Test that subclass handlers override parent handlers."""
    assume(chain_length >= 3)
    
    chain = create_inheritance_chain(chain_length)
    
    @functools.singledispatch
    def test_func(arg):
        return "default"
    
    # Register handler for base
    @test_func.register(chain[0])
    def base_handler(arg):
        return "base"
    
    # Register handler for middle class
    middle_idx = chain_length // 2
    @test_func.register(chain[middle_idx])
    def middle_handler(arg):
        return "middle"
    
    # Test resolution
    for i, cls in enumerate(chain):
        instance = cls()
        result = test_func(instance)
        
        if i < middle_idx:
            assert result == "base"
        else:
            assert result == "middle"


@given(type_and_value())
def test_single_dispatch_on_first_arg(type_and_val):
    """Test that singledispatch only considers the first argument's type."""
    target_type, target_value = type_and_val
    
    @functools.singledispatch
    def test_func(arg1, arg2=None, arg3=None):
        return "default"
    
    @test_func.register(target_type)
    def typed_handler(arg1, arg2=None, arg3=None):
        return f"typed_{target_type.__name__}"
    
    # Property: dispatch depends only on first argument type
    result1 = test_func(target_value)
    result2 = test_func(target_value, "extra", "args")
    result3 = test_func(target_value, arg2=123, arg3=456)
    
    expected = f"typed_{target_type.__name__}"
    assert result1 == expected
    assert result2 == expected
    assert result3 == expected
    
    # Different first arg type should give default
    if target_type != str:
        assert test_func("different") == "default"


@given(st.sampled_from([int, str, list, dict, float, type(None)]))
def test_none_type_registration(other_type):
    """Test that None type can be properly registered and dispatched."""
    
    @functools.singledispatch
    def test_func(arg):
        return "default"
    
    @test_func.register(type(None))
    def none_handler(arg):
        return "none_handler"
    
    if other_type != type(None):
        @test_func.register(other_type)
        def other_handler(arg):
            return f"handler_for_{other_type.__name__}"
    
    # Test None dispatches correctly
    assert test_func(None) == "none_handler"
    
    # Test other types still work
    if other_type == int:
        assert test_func(42) == "handler_for_int"
    elif other_type == str:
        assert test_func("test") == "handler_for_str"
    elif other_type == list:
        assert test_func([]) == "handler_for_list"
    elif other_type == dict:
        assert test_func({}) == "handler_for_dict"
    elif other_type == float:
        assert test_func(3.14) == "handler_for_float"


@given(
    st.lists(
        st.sampled_from([int, str, list, dict, float, bool, tuple, set]),
        min_size=1,
        max_size=5,
        unique=True
    )
)
def test_registry_immutability(types_to_register):
    """Test that the registry returned is immutable (actually a MappingProxy)."""
    
    @functools.singledispatch
    def test_func(arg):
        return "default"
    
    # Register some handlers
    for typ in types_to_register:
        @test_func.register(typ)
        def handler(arg):
            return f"handler_for_{typ.__name__}"
    
    # Property: registry should be a MappingProxy (immutable view)
    registry = test_func.registry
    
    # Check it's a MappingProxy
    from types import MappingProxyType
    assert isinstance(registry, MappingProxyType)
    
    # Try to modify it - should raise error
    try:
        registry[int] = lambda x: "hacked"
        assert False, "Registry should be immutable"
    except (TypeError, AttributeError):
        pass  # Expected


@given(st.integers(1, 100))
def test_dispatch_cache_behavior(num_lookups):
    """Test that dispatch lookups are consistent across multiple calls."""
    
    @functools.singledispatch
    def test_func(arg):
        return "default"
    
    @test_func.register(int)
    def int_handler(arg):
        return "int"
    
    @test_func.register(str)
    def str_handler(arg):
        return "str"
    
    # Property: Multiple dispatch calls for same type should return same handler
    handlers_for_int = []
    handlers_for_str = []
    
    for _ in range(num_lookups):
        handlers_for_int.append(test_func.dispatch(int))
        handlers_for_str.append(test_func.dispatch(str))
    
    # All handlers for same type should be identical
    assert all(h is handlers_for_int[0] for h in handlers_for_int)
    assert all(h is handlers_for_str[0] for h in handlers_for_str)
    
    # And they should be the registered handlers
    assert handlers_for_int[0] is int_handler
    assert handlers_for_str[0] is str_handler


def test_abc_virtual_subclass_registration():
    """Test that ABC virtual subclasses work with singledispatch."""
    from collections.abc import Sized
    
    @functools.singledispatch
    def get_size(obj):
        return -1
    
    @get_size.register(Sized)
    def _(obj):
        return len(obj)
    
    # Built-in types that are Sized
    assert get_size([1, 2, 3]) == 3
    assert get_size("hello") == 5
    assert get_size({1, 2}) == 2
    assert get_size({"a": 1}) == 1
    
    # Custom class implementing __len__
    class CustomSized:
        def __len__(self):
            return 42
    
    assert get_size(CustomSized()) == 42
    
    # Non-sized objects
    assert get_size(42) == -1
    assert get_size(3.14) == -1