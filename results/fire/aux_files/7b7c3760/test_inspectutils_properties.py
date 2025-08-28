"""Property-based tests for fire.inspectutils module using Hypothesis."""

import collections
import inspect
import os
import sys
import types
from typing import Any

import pytest
from hypothesis import assume, given, settings, strategies as st

# Add fire_env to path
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')
import fire.inspectutils as inspectutils


# Strategy for generating various Python objects
@st.composite
def python_objects(draw):
    """Generate various Python objects to test with."""
    choice = draw(st.integers(0, 10))
    
    if choice == 0:
        # Built-in types
        return draw(st.sampled_from([int, str, list, dict, tuple, set, float, bool]))
    elif choice == 1:
        # Built-in functions
        return draw(st.sampled_from([len, abs, print, type, isinstance, getattr]))
    elif choice == 2:
        # Simple values
        return draw(st.one_of(st.integers(), st.floats(allow_nan=False), st.text(), st.booleans()))
    elif choice == 3:
        # Lists and tuples
        return draw(st.one_of(st.lists(st.integers()), st.tuples(st.integers())))
    elif choice == 4:
        # Classes
        class TestClass:
            def __init__(self, x=5):
                self.x = x
            def method(self, y):
                return self.x + y
        return TestClass
    elif choice == 5:
        # Functions
        def test_func(a, b=10, *args, **kwargs):
            return a + b
        return test_func
    elif choice == 6:
        # Lambda functions
        return lambda x, y=5: x + y
    elif choice == 7:
        # Methods
        class TestClass:
            def method(self, x):
                return x * 2
        return TestClass().method
    elif choice == 8:
        # Namedtuples
        Point = collections.namedtuple('Point', ['x', 'y'])
        return draw(st.sampled_from([Point, Point(1, 2)]))
    elif choice == 9:
        # Module
        return draw(st.sampled_from([os, sys, types, collections]))
    else:
        # Callable objects
        class Callable:
            def __call__(self, x):
                return x
        return Callable()


@st.composite
def callable_objects(draw):
    """Generate callable objects for testing GetFullArgSpec."""
    choice = draw(st.integers(0, 7))
    
    if choice == 0:
        # Simple function
        def func(a, b=10, *args, **kwargs):
            return a
        return func
    elif choice == 1:
        # Lambda
        return lambda x, y=5: x + y
    elif choice == 2:
        # Built-in function
        return draw(st.sampled_from([len, abs, print, type, max, min]))
    elif choice == 3:
        # Class with __init__
        class TestClass:
            def __init__(self, x=5, y=10):
                self.x = x
        return TestClass
    elif choice == 4:
        # Bound method
        class TestClass:
            def method(self, x, y=2):
                return x * y
        return TestClass().method
    elif choice == 5:
        # Class without __init__ (uses default)
        class SimpleClass:
            pass
        return SimpleClass
    elif choice == 6:
        # Callable object
        class CallableObj:
            def __call__(self, a, b=1):
                return a + b
        return CallableObj()
    else:
        # String methods (builtins)
        return draw(st.sampled_from(['test'.upper, 'test'.lower, 'test'.strip]))


# Test 1: GetFullArgSpec returns consistent FullArgSpec structure
@given(callable_objects())
def test_getfullargspec_returns_fullargspec(fn):
    """GetFullArgSpec should return a FullArgSpec with the expected attributes."""
    try:
        spec = inspectutils.GetFullArgSpec(fn)
    except (TypeError, AttributeError, ValueError):
        # Some objects might not support inspection
        return
    
    # Check that spec has all required attributes
    assert hasattr(spec, 'args')
    assert hasattr(spec, 'varargs')
    assert hasattr(spec, 'varkw')
    assert hasattr(spec, 'defaults')
    assert hasattr(spec, 'kwonlyargs')
    assert hasattr(spec, 'kwonlydefaults')
    assert hasattr(spec, 'annotations')
    
    # Type invariants
    assert isinstance(spec.args, list)
    assert all(isinstance(arg, str) for arg in spec.args)
    assert spec.varargs is None or isinstance(spec.varargs, str)
    assert spec.varkw is None or isinstance(spec.varkw, str)
    assert spec.defaults is None or isinstance(spec.defaults, tuple)
    assert isinstance(spec.kwonlyargs, list)
    assert all(isinstance(arg, str) for arg in spec.kwonlyargs)
    assert spec.kwonlydefaults is None or isinstance(spec.kwonlydefaults, dict)
    assert isinstance(spec.annotations, dict)


# Test 2: GetFullArgSpec defaults correspondence invariant
@given(callable_objects())
def test_getfullargspec_defaults_correspondence(fn):
    """If there are N defaults, they should correspond to the last N args."""
    try:
        spec = inspectutils.GetFullArgSpec(fn)
    except (TypeError, AttributeError, ValueError):
        return
    
    if spec.defaults and spec.args:
        # Number of defaults should not exceed number of args
        assert len(spec.defaults) <= len(spec.args)


# Test 3: IsNamedTuple properties
@given(python_objects())
def test_isnamedtuple_consistency(obj):
    """IsNamedTuple should correctly identify namedtuples."""
    result = inspectutils.IsNamedTuple(obj)
    
    # Result should be boolean
    assert isinstance(result, bool)
    
    # If it's a namedtuple, it must be a tuple
    if result:
        assert isinstance(obj, tuple)
        assert hasattr(obj, '_fields')
    
    # Regular tuples without _fields should return False
    if isinstance(obj, tuple) and not hasattr(obj, '_fields'):
        assert not result


# Test 4: IsNamedTuple with actual namedtuples
@given(st.text(min_size=1, max_size=10).filter(str.isidentifier),
       st.lists(st.text(min_size=1, max_size=10).filter(str.isidentifier), min_size=1, max_size=5, unique=True))
def test_isnamedtuple_with_real_namedtuples(name, fields):
    """Test with dynamically created namedtuples."""
    # Create a namedtuple class
    NT = collections.namedtuple(name, fields)
    
    # The class itself should not be identified as a namedtuple
    assert not inspectutils.IsNamedTuple(NT)
    
    # But instances should be
    values = list(range(len(fields)))
    instance = NT(*values)
    assert inspectutils.IsNamedTuple(instance)


# Test 5: Info function invariants
@given(python_objects())
def test_info_returns_dict_with_required_fields(obj):
    """Info should always return a dict with certain fields."""
    info = inspectutils.Info(obj)
    
    # Should return a dict
    assert isinstance(info, dict)
    
    # Required fields that should always be present
    assert 'type_name' in info
    assert 'string_form' in info
    
    # Type invariants
    assert isinstance(info['type_name'], str)
    assert isinstance(info['string_form'], str)
    
    # string_form should match str(obj)
    assert info['string_form'] == str(obj)
    
    # Optional fields should have correct types if present
    if 'file' in info:
        assert info['file'] is None or isinstance(info['file'], str)
    if 'line' in info:
        assert info['line'] is None or (isinstance(info['line'], int) and info['line'] > 0)
    if 'docstring' in info:
        assert info['docstring'] is None or isinstance(info['docstring'], str)


# Test 6: GetFileAndLine properties
@given(python_objects())
def test_getfileandline_invariants(component):
    """GetFileAndLine should return consistent filename/line pairs."""
    filename, lineno = inspectutils.GetFileAndLine(component)
    
    # Both None or both not None for many cases
    if filename is None:
        # Builtins and some other types return (None, None)
        pass
    else:
        # Filename should be a string
        assert isinstance(filename, str)
    
    if lineno is not None:
        # Line number should be positive
        assert isinstance(lineno, int)
        assert lineno > 0


# Test 7: GetClassAttrsDict properties
@given(python_objects())
def test_getclassattrsdict_properties(component):
    """GetClassAttrsDict should return None for non-classes, dict for classes."""
    result = inspectutils.GetClassAttrsDict(component)
    
    if inspect.isclass(component):
        # Should return a dict for classes
        assert isinstance(result, dict)
        # All keys should be strings (attribute names)
        assert all(isinstance(key, str) for key in result.keys())
    else:
        # Should return None for non-classes
        assert result is None


# Test 8: IsCoroutineFunction robustness
@given(python_objects())
def test_iscoroutinefunction_no_crash(fn):
    """IsCoroutineFunction should never crash and return boolean."""
    result = inspectutils.IsCoroutineFunction(fn)
    assert isinstance(result, bool)


# Test 9: Test with async functions (property test)
@pytest.mark.asyncio
@given(st.integers())
async def test_iscoroutinefunction_async_detection(x):
    """Test that async functions are correctly detected."""
    async def async_func(n):
        return n * 2
    
    def sync_func(n):
        return n * 2
    
    # Async function should be detected
    assert inspectutils.IsCoroutineFunction(async_func) == True
    
    # Regular function should not be detected as coroutine
    assert inspectutils.IsCoroutineFunction(sync_func) == False


# Test 10: Multiple calls with same input should give same result (determinism)
@given(callable_objects())
def test_getfullargspec_deterministic(fn):
    """Multiple calls to GetFullArgSpec should return the same result."""
    try:
        spec1 = inspectutils.GetFullArgSpec(fn)
        spec2 = inspectutils.GetFullArgSpec(fn)
    except (TypeError, AttributeError, ValueError):
        return
    
    # Should get the same result
    assert spec1.args == spec2.args
    assert spec1.varargs == spec2.varargs
    assert spec1.varkw == spec2.varkw
    assert spec1.defaults == spec2.defaults
    assert spec1.kwonlyargs == spec2.kwonlyargs
    assert spec1.kwonlydefaults == spec2.kwonlydefaults
    assert spec1.annotations == spec2.annotations


# Test 11: FullArgSpec constructor property
@given(
    st.lists(st.text(min_size=1, max_size=10)),
    st.one_of(st.none(), st.text(min_size=1, max_size=10)),
    st.one_of(st.none(), st.text(min_size=1, max_size=10)),
    st.one_of(st.none(), st.tuples(st.integers())),
    st.lists(st.text(min_size=1, max_size=10)),
    st.one_of(st.none(), st.dictionaries(st.text(min_size=1), st.integers())),
    st.dictionaries(st.text(min_size=1), st.text())
)
def test_fullargspec_constructor(args, varargs, varkw, defaults, kwonlyargs, kwonlydefaults, annotations):
    """Test FullArgSpec constructor maintains data correctly."""
    spec = inspectutils.FullArgSpec(
        args=args,
        varargs=varargs,
        varkw=varkw,
        defaults=defaults,
        kwonlyargs=kwonlyargs,
        kwonlydefaults=kwonlydefaults,
        annotations=annotations
    )
    
    # Check that all fields are set correctly
    assert spec.args == args
    assert spec.varargs == varargs
    assert spec.varkw == varkw
    if defaults is None:
        assert spec.defaults == ()
    else:
        assert spec.defaults == defaults
    assert spec.kwonlyargs == kwonlyargs
    if kwonlydefaults is None:
        assert spec.kwonlydefaults == {}
    else:
        assert spec.kwonlydefaults == kwonlydefaults
    assert spec.annotations == annotations


if __name__ == '__main__':
    # Run a quick test
    pytest.main([__file__, '-v'])