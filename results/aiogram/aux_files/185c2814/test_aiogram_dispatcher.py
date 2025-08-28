#!/usr/bin/env python3
"""Property-based tests for aiogram.dispatcher module"""

import sys
import os
import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from typing import Dict, Any, List
import string

# Add the virtualenv to the path
sys.path.insert(0, '/root/hypothesis-llm/envs/aiogram_env/lib/python3.13/site-packages')

from aiogram.dispatcher.dispatcher import Dispatcher
from aiogram.dispatcher.router import Router
from aiogram.dispatcher.flags import FlagDecorator, Flag, FlagGenerator, extract_flags_from_object


# ====== Router Properties ======

@given(st.text(min_size=1, max_size=50))
def test_router_no_self_reference(name):
    """Test that a router cannot be its own parent (router.py:213)"""
    router = Router(name=name)
    with pytest.raises(RuntimeError, match="Self-referencing routers is not allowed"):
        router.parent_router = router


@given(st.integers(min_value=2, max_value=10))
def test_router_no_circular_reference(chain_length):
    """Test that circular router references are not allowed (router.py:218)"""
    routers = [Router(name=f"router_{i}") for i in range(chain_length)]
    
    # Create a chain
    for i in range(chain_length - 1):
        routers[i].include_router(routers[i + 1])
    
    # Try to create a circular reference
    with pytest.raises(RuntimeError, match="Circular referencing of Router is not allowed"):
        routers[-1].include_router(routers[0])


@given(st.text(min_size=1, max_size=50))
def test_router_parent_uniqueness(name):
    """Test that a router can only have one parent (router.py:211)"""
    router = Router(name=name)
    parent1 = Router(name="parent1")
    parent2 = Router(name="parent2")
    
    parent1.include_router(router)
    
    # Router already has parent1, cannot be attached to parent2
    with pytest.raises(RuntimeError, match="Router is already attached"):
        parent2.include_router(router)


@given(st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=5))
def test_router_chain_consistency(names):
    """Test that router chains are consistent"""
    routers = [Router(name=name) for name in names]
    
    # Create a chain
    for i in range(len(routers) - 1):
        routers[i].include_router(routers[i + 1])
    
    # Check chain_head consistency
    for i, router in enumerate(routers):
        chain = list(router.chain_head)
        assert len(chain) == i + 1
        assert chain[0] == router
        if i > 0:
            assert chain[-1] == routers[0]
    
    # Check chain_tail consistency  
    tail = list(routers[0].chain_tail)
    assert len(tail) == len(routers)
    assert tail == routers


@given(st.lists(st.text(min_size=1, max_size=20), min_size=2, max_size=5))
def test_router_include_routers_multiple(names):
    """Test including multiple routers at once"""
    parent = Router(name="parent")
    child_routers = [Router(name=name) for name in names]
    
    parent.include_routers(*child_routers)
    
    assert len(parent.sub_routers) == len(child_routers)
    for router in child_routers:
        assert router.parent_router == parent
        assert router in parent.sub_routers


# ====== Dispatcher Properties ======

@given(
    st.dictionaries(
        st.text(min_size=1, max_size=20),
        st.one_of(st.integers(), st.text(), st.booleans()),
        min_size=0,
        max_size=10
    )
)
def test_dispatcher_dict_operations(workflow_data):
    """Test that Dispatcher supports dictionary-like operations"""
    dispatcher = Dispatcher(**workflow_data)
    
    # Test __getitem__, __setitem__, __delitem__
    for key, value in workflow_data.items():
        assert dispatcher[key] == value
        assert dispatcher.get(key) == value
    
    # Test setting new values
    new_key = "test_key_new"
    new_value = "test_value"
    dispatcher[new_key] = new_value
    assert dispatcher[new_key] == new_value
    
    # Test deleting
    if workflow_data:
        key_to_delete = list(workflow_data.keys())[0]
        del dispatcher[key_to_delete]
        with pytest.raises(KeyError):
            _ = dispatcher[key_to_delete]
        assert dispatcher.get(key_to_delete) is None


def test_dispatcher_invalid_storage():
    """Test that Dispatcher validates storage type (dispatcher.py:62)"""
    invalid_storage = "not_a_storage"  # String instead of BaseStorage
    
    with pytest.raises(TypeError, match="FSM storage should be instance of 'BaseStorage'"):
        Dispatcher(storage=invalid_storage)


def test_dispatcher_no_parent_router():
    """Test that Dispatcher cannot have a parent router (dispatcher.py:133)"""
    dispatcher = Dispatcher()
    router = Router()
    
    with pytest.raises(RuntimeError, match="Dispatcher can not be attached to another Router"):
        dispatcher.parent_router = router


# ====== Flag Properties ======

@given(st.text(alphabet=string.ascii_letters + string.digits, min_size=1, max_size=20))
def test_flag_name_no_underscore(name):
    """Test that flag names cannot start with underscore (flags.py:73)"""
    generator = FlagGenerator()
    
    if name.startswith("_"):
        with pytest.raises(AttributeError, match="Flag name must NOT start with underscore"):
            getattr(generator, name)
    else:
        flag_decorator = getattr(generator, name)
        assert isinstance(flag_decorator, FlagDecorator)
        assert flag_decorator.flag.name == name
        assert flag_decorator.flag.value is True


@given(
    st.one_of(st.integers(), st.text(), st.booleans()),
    st.dictionaries(st.text(min_size=1), st.integers(), min_size=1, max_size=3)
)
def test_flag_decorator_value_kwargs_exclusive(value, kwargs):
    """Test that FlagDecorator can't use both value and kwargs (flags.py:46)"""
    flag = Flag("test_flag", True)
    decorator = FlagDecorator(flag)
    
    # Should raise ValueError when both value and kwargs are provided
    def dummy_func():
        pass
    
    with pytest.raises(ValueError, match="The arguments `value` and \\*\\*kwargs can not be used together"):
        decorator(value, **kwargs)


@given(st.text(min_size=1, max_size=20))
def test_flag_decorator_callable_decoration(flag_name):
    """Test that FlagDecorator properly decorates callable objects"""
    generator = FlagGenerator()
    flag_decorator = getattr(generator, flag_name)
    
    def test_function():
        return "test"
    
    decorated = flag_decorator(test_function)
    
    # Function should still be callable
    assert callable(decorated)
    assert decorated() == "test"
    
    # Should have the flag attached
    flags = extract_flags_from_object(decorated)
    assert flag_name in flags
    assert flags[flag_name] is True


@given(
    st.dictionaries(
        st.text(min_size=1, max_size=10),
        st.one_of(st.integers(), st.text(), st.booleans()),
        min_size=1,
        max_size=5
    )
)
def test_flag_decorator_with_kwargs(flag_data):
    """Test FlagDecorator with keyword arguments"""
    flag = Flag("test_flag", True)
    decorator = FlagDecorator(flag)
    
    # Create decorator with kwargs
    new_decorator = decorator(**flag_data)
    assert isinstance(new_decorator, FlagDecorator)
    
    # Value should be an AttrDict with the kwargs
    from magic_filter import AttrDict
    assert isinstance(new_decorator.flag.value, AttrDict)
    for key, value in flag_data.items():
        assert new_decorator.flag.value[key] == value


# ====== Router Type Validation ======

@given(st.one_of(st.integers(), st.text(), st.lists(st.integers())))
def test_router_include_invalid_type(invalid_router):
    """Test that include_router validates router type"""
    router = Router()
    
    with pytest.raises(ValueError, match="router should be instance of Router"):
        router.include_router(invalid_router)


@given(st.lists(st.one_of(st.integers(), st.text()), min_size=1, max_size=3))
def test_router_include_routers_invalid_types(invalid_routers):
    """Test that include_routers validates all router types"""
    router = Router()
    
    with pytest.raises(ValueError, match="router should be instance of Router"):
        router.include_routers(*invalid_routers)


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])