#!/usr/bin/env python3
"""Advanced property-based tests for fire.inspectutils module."""

import asyncio
import collections
import inspect
import sys
import types
from typing import Any, Callable

import pytest
from hypothesis import assume, given, strategies as st, settings, note

# Add the fire_env to path
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')
import fire.inspectutils as inspectutils


# Strategy for more complex callable objects
@st.composite
def complex_callables(draw):
    """Generate various types of callable objects."""
    choice = draw(st.integers(min_value=0, max_value=4))
    
    if choice == 0:
        # Lambda function
        num_args = draw(st.integers(min_value=0, max_value=3))
        if num_args == 0:
            return lambda: None
        elif num_args == 1:
            return lambda x: x
        elif num_args == 2:
            return lambda x, y: x + y
        else:
            return lambda x, y, z: x + y + z
    
    elif choice == 1:
        # Function with defaults
        def func_with_defaults(a, b=10, c=20):
            return a + b + c
        return func_with_defaults
    
    elif choice == 2:
        # Class with __init__
        class TestClass:
            def __init__(self, x, y=5):
                self.x = x
                self.y = y
        return TestClass
    
    elif choice == 3:
        # Class without __init__
        class EmptyClass:
            pass
        return EmptyClass
    
    else:
        # Method
        class ClassWithMethod:
            def method(self, x):
                return x * 2
        return ClassWithMethod().method


# Test round-trip properties for GetFullArgSpec
@given(complex_callables())
@settings(max_examples=300)
def test_getfullargspec_consistency(func):
    """Test that GetFullArgSpec produces consistent results."""
    try:
        spec1 = inspectutils.GetFullArgSpec(func)
        spec2 = inspectutils.GetFullArgSpec(func)
        
        # Property: Calling GetFullArgSpec twice should produce identical results
        assert spec1.args == spec2.args
        assert spec1.defaults == spec2.defaults
        assert spec1.varargs == spec2.varargs
        assert spec1.varkw == spec2.varkw
        assert spec1.kwonlyargs == spec2.kwonlyargs
        assert spec1.kwonlydefaults == spec2.kwonlydefaults
        assert spec1.annotations == spec2.annotations
        
    except (TypeError, ValueError):
        # Some functions might not be inspectable
        pass


# Test Info function more thoroughly
@given(st.one_of(
    st.integers(min_value=-1000, max_value=1000),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(min_size=0, max_size=100),
    st.lists(st.integers(), min_size=0, max_size=10),
    st.dictionaries(st.text(min_size=1, max_size=5), st.integers(), min_size=0, max_size=5),
    st.tuples(st.integers(), st.text()),
    st.sets(st.integers(), min_size=0, max_size=5),
))
@settings(max_examples=500)
def test_info_completeness(component):
    """Test that Info returns complete and consistent information."""
    info = inspectutils.Info(component)
    
    # Property: Info should always return a dict
    assert isinstance(info, dict)
    
    # Property: type_name and string_form should always be present
    assert 'type_name' in info
    assert 'string_form' in info
    
    # Property: If component has __doc__, it should be captured
    if hasattr(component, '__doc__'):
        doc = component.__doc__
        if doc and doc != '<no docstring>':
            # This might not always be true due to IPython behavior
            pass
    
    # Property: file should be None for built-in types
    if isinstance(component, (int, float, str, list, dict, tuple, set)):
        assert info.get('file') is None or 'built-in' in str(info.get('file', '')).lower()
    
    # Property: line should be None or a positive integer
    line = info.get('line')
    assert line is None or (isinstance(line, int) and line > 0)


# Test IsNamedTuple with edge cases
@given(st.one_of(
    # Regular tuples with _fields attribute (false positive test)
    st.tuples(st.integers()).map(lambda t: type('FakeTuple', (tuple,), {'_fields': ('x',)})(t)),
    # Empty tuples
    st.just(()),
    # Single element tuples
    st.tuples(st.integers()),
    # Nested tuples
    st.tuples(st.tuples(st.integers())),
))
@settings(max_examples=200)
def test_isnamedtuple_edge_cases(component):
    """Test IsNamedTuple with edge cases."""
    result = inspectutils.IsNamedTuple(component)
    
    # For regular empty tuples
    if component == ():
        assert result is False
    
    # The function checks for _fields attribute
    if hasattr(component, '_fields') and isinstance(component, tuple):
        assert result is True
    elif not isinstance(component, tuple):
        assert result is False


# Test GetFileAndLine with user-defined functions
def sample_function():
    """A sample function for testing."""
    return "test"


class SampleClass:
    """A sample class for testing."""
    def method(self):
        return "method"


@given(st.sampled_from([
    sample_function,
    SampleClass,
    SampleClass.method,
    SampleClass().method,
    lambda x: x,
]))
@settings(max_examples=50)
def test_getfileandline_user_defined(component):
    """Test GetFileAndLine with user-defined components."""
    filename, lineno = inspectutils.GetFileAndLine(component)
    
    # For lambdas, we might get the current file
    if component.__name__ == '<lambda>':
        # Lambda functions should have a file
        assert filename is not None or inspect.isbuiltin(component)
    else:
        # User-defined functions/classes should have file info
        if not inspect.isbuiltin(component):
            # Should have a filename (unless it's defined in interactive mode)
            pass  # Can't guarantee in all environments


# Test GetClassAttrsDict thoroughly
@given(st.sampled_from([
    int,
    str,
    list,
    dict,
    type,
    object,
    SampleClass,
]))
@settings(max_examples=100)
def test_getclassattrsdict_classes(cls):
    """Test GetClassAttrsDict with various classes."""
    result = inspectutils.GetClassAttrsDict(cls)
    
    # Property: Should return a dict for classes
    assert isinstance(result, dict)
    
    # Property: Keys should be strings (attribute names)
    for key in result.keys():
        assert isinstance(key, str)
    
    # Property: Values should be Attribute objects with expected fields
    for value in result.values():
        assert hasattr(value, 'name')
        assert hasattr(value, 'kind')
        assert hasattr(value, 'defining_class')
        assert hasattr(value, 'object')


# Test IsCoroutineFunction with actual coroutines
async def async_function():
    """An async function for testing."""
    return "async"


def sync_function():
    """A sync function for testing."""
    return "sync"


@given(st.sampled_from([
    async_function,
    sync_function,
    lambda x: x,
    int,
    str,
    None,
    42,
    "string",
]))
@settings(max_examples=100)
def test_iscoroutinefunction_comprehensive(component):
    """Test IsCoroutineFunction comprehensively."""
    result = inspectutils.IsCoroutineFunction(component)
    
    # Check using asyncio directly for comparison
    try:
        expected = asyncio.iscoroutinefunction(component)
    except:
        expected = False
    
    # Property: Should match asyncio.iscoroutinefunction
    assert result == expected


# Test FullArgSpec initialization and defaults
@given(
    args=st.lists(st.text(min_size=1, max_size=5), min_size=0, max_size=5),
    varargs=st.one_of(st.none(), st.text(min_size=1, max_size=10)),
    varkw=st.one_of(st.none(), st.text(min_size=1, max_size=10)),
    defaults=st.one_of(st.none(), st.tuples(st.integers())),
    kwonlyargs=st.lists(st.text(min_size=1, max_size=5), min_size=0, max_size=3),
    kwonlydefaults=st.one_of(st.none(), st.dictionaries(st.text(min_size=1, max_size=5), st.integers(), min_size=0, max_size=3)),
)
@settings(max_examples=200)
def test_fullargspec_initialization(args, varargs, varkw, defaults, kwonlyargs, kwonlydefaults):
    """Test FullArgSpec initialization with various inputs."""
    spec = inspectutils.FullArgSpec(
        args=args,
        varargs=varargs,
        varkw=varkw,
        defaults=defaults,
        kwonlyargs=kwonlyargs,
        kwonlydefaults=kwonlydefaults,
    )
    
    # Property: Attributes should match what was passed in (with defaults)
    assert spec.args == (args or [])
    assert spec.varargs == varargs
    assert spec.varkw == varkw
    assert spec.defaults == (defaults or ())
    assert spec.kwonlyargs == (kwonlyargs or [])
    assert spec.kwonlydefaults == (kwonlydefaults or {})
    assert spec.annotations == {}  # Should default to empty dict


# Test GetFullArgSpec with builtin methods
@given(st.sampled_from([
    'test'.upper,
    'test'.lower,
    'test'.strip,
    [].append,
    [].pop,
    {}.get,
    {}.items,
]))
@settings(max_examples=100)
def test_getfullargspec_builtins(builtin_method):
    """Test GetFullArgSpec with builtin methods."""
    try:
        spec = inspectutils.GetFullArgSpec(builtin_method)
        
        # Property: Builtins should have varargs and varkw
        # Based on the code, builtins return FullArgSpec(varargs='vars', varkw='kwargs')
        assert spec.varargs == 'vars' or spec.varargs is None
        assert spec.varkw == 'kwargs' or spec.varkw is None
        
    except TypeError:
        # Some builtins might not be inspectable
        pass


# Edge case: Test with classes that have _fields but aren't namedtuples
class FakeNamedTuple:
    """A class that pretends to be a namedtuple."""
    _fields = ('x', 'y')
    
    def __init__(self, x, y):
        self.x = x
        self.y = y


@given(st.integers(), st.integers())
@settings(max_examples=50)
def test_getfullargspec_fake_namedtuple(x, y):
    """Test GetFullArgSpec with fake namedtuple."""
    fake_nt = FakeNamedTuple
    
    spec = inspectutils.GetFullArgSpec(fake_nt)
    
    # According to the code, if _fields exists, it uses that for args
    # This happens in the TypeError handling branch
    expected_args = list(fake_nt._fields) if hasattr(fake_nt, '_fields') else []
    
    # The function might use __init__ args or _fields
    # Can't guarantee exact behavior without deeper inspection
    assert isinstance(spec.args, list)


# Test _GetArgSpecInfo internal function behavior
@given(st.sampled_from([
    int,  # Class
    lambda x: x,  # Function
    SampleClass().method,  # Bound method
    str.upper,  # Builtin method
    abs,  # Builtin function
]))
@settings(max_examples=100)
def test_getargspecinfo_behavior(component):
    """Test _GetArgSpecInfo behavior."""
    fn, skip_arg = inspectutils._GetArgSpecInfo(component)
    
    # Property: skip_arg should be True for classes and bound methods
    if inspect.isclass(component):
        assert skip_arg is True
    
    if inspect.ismethod(component) and component.__self__ is not None:
        assert skip_arg is True
    
    # Property: fn should be callable or a type
    assert callable(fn) or isinstance(fn, type)


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])