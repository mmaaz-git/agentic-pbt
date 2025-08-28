"""Property-based tests for limits.typing module"""

import sys
import importlib
from hypothesis import given, strategies as st, settings

# Add the virtual environment's site-packages to the path
sys.path.insert(0, '/root/hypothesis-llm/envs/limits_env/lib/python3.13/site-packages')

import limits.typing


def test_all_exports_are_defined():
    """Test that all items in __all__ are actually defined in the module"""
    module = limits.typing
    all_exports = module.__all__
    
    for name in all_exports:
        assert hasattr(module, name), f"Name '{name}' is in __all__ but not defined in module"
        # Verify we can actually access it
        attr = getattr(module, name)
        assert attr is not None or name == "Any", f"Export '{name}' is None unexpectedly"


def test_all_exports_can_be_imported():
    """Test that all items in __all__ can be imported using from limits.typing import *"""
    # Simulate from limits.typing import *
    module = limits.typing
    namespace = {}
    
    if hasattr(module, '__all__'):
        for name in module.__all__:
            if hasattr(module, name):
                namespace[name] = getattr(module, name)
    
    # Verify all __all__ items made it to namespace
    for name in module.__all__:
        assert name in namespace, f"Failed to import '{name}' from __all__"


def test_serializable_type_components():
    """Test that Serializable type alias components are accessible"""
    # Serializable is defined as int | str | float
    # We can't directly test type aliases at runtime, but we can verify 
    # that the type exists and basic properties
    assert hasattr(limits.typing, 'Serializable')
    serializable = limits.typing.Serializable
    
    # In Python 3.10+, we can inspect union types
    if sys.version_info >= (3, 10):
        import types
        if hasattr(types, 'UnionType'):
            # Verify it's a union type (though we can't easily inspect its contents)
            assert serializable is not None


def test_protocol_classes_are_protocols():
    """Test that Protocol classes are actually Protocol subclasses"""
    from typing import Protocol, runtime_checkable
    
    # Check MemcachedClientP
    assert hasattr(limits.typing, 'MemcachedClientP')
    memcached_protocol = limits.typing.MemcachedClientP
    
    # Verify it's a Protocol (checking the base classes)
    assert Protocol in memcached_protocol.__mro__, "MemcachedClientP should be a Protocol"


def test_type_variables_exist():
    """Test that type variables R, R_co, and P are defined"""
    from typing import TypeVar, ParamSpec
    
    # Check R
    assert hasattr(limits.typing, 'R')
    R = limits.typing.R
    assert isinstance(R, TypeVar), "R should be a TypeVar"
    
    # Check R_co 
    assert hasattr(limits.typing, 'R_co')
    R_co = limits.typing.R_co
    assert isinstance(R_co, TypeVar), "R_co should be a TypeVar"
    # Verify it's covariant
    assert R_co.__covariant__ == True, "R_co should be covariant"
    
    # Check P
    assert hasattr(limits.typing, 'P')
    P = limits.typing.P
    assert isinstance(P, ParamSpec), "P should be a ParamSpec"


@given(st.sampled_from(limits.typing.__all__))
def test_each_export_individually(export_name):
    """Property test: each item in __all__ should be importable individually"""
    # This tests that we can import each export
    assert hasattr(limits.typing, export_name), f"{export_name} not found in module"
    
    # Try to get the attribute
    attr = getattr(limits.typing, export_name)
    
    # Basic smoke test - the attribute should exist
    # We don't check for None because 'Any' can be None-like in some contexts
    if export_name not in ['Any', 'TYPE_CHECKING']:
        assert attr is not None, f"Export '{export_name}' is unexpectedly None"


def test_counter_is_collections_counter():
    """Test that Counter exported is the same as collections.Counter"""
    from collections import Counter as CollectionsCounter
    
    assert hasattr(limits.typing, 'Counter')
    limits_counter = limits.typing.Counter
    
    # They should be the same class
    assert limits_counter is CollectionsCounter, "Counter should be collections.Counter"


def test_reexported_typing_items():
    """Test that items re-exported from typing module match the originals"""
    import typing
    from collections.abc import Awaitable as AbcAwaitable, Callable as AbcCallable, Iterable as AbcIterable
    
    typing_exports = [
        'TYPE_CHECKING', 'Any', 'ClassVar',
        'Literal', 'NamedTuple', 'ParamSpec', 'Protocol',
        'TypeAlias', 'TypeVar', 'cast'
    ]
    
    # Items from collections.abc
    abc_exports = {
        'Awaitable': AbcAwaitable,
        'Callable': AbcCallable, 
        'Iterable': AbcIterable
    }
    
    # Check typing module exports
    for name in typing_exports:
        if name in limits.typing.__all__:
            limits_attr = getattr(limits.typing, name, None)
            typing_attr = getattr(typing, name, None) if hasattr(typing, name) else None
            
            if limits_attr is not None and typing_attr is not None:
                assert limits_attr is typing_attr, f"{name} should be the same as in typing module"
    
    # Check collections.abc exports
    for name, expected in abc_exports.items():
        if name in limits.typing.__all__:
            limits_attr = getattr(limits.typing, name, None)
            assert limits_attr is expected, f"{name} should be from collections.abc"


if __name__ == "__main__":
    # Run all tests
    test_all_exports_are_defined()
    test_all_exports_can_be_imported()
    test_serializable_type_components()
    test_protocol_classes_are_protocols()
    test_type_variables_exist()
    test_counter_is_collections_counter()
    test_reexported_typing_items()
    
    # Run property test
    test_each_export_individually()
    
    print("All tests passed!")