#!/usr/bin/env python3
"""Edge case tests for fire.inspectutils focusing on potential bugs."""

import collections
import inspect
import sys
import types

import pytest
from hypothesis import assume, given, strategies as st, settings, example

sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')
import fire.inspectutils as inspectutils


# Test Python 3 keyword-only arguments
def test_kwonly_args_handling():
    """Test handling of keyword-only arguments."""
    
    def func_with_kwonly(a, b, *, c, d=10):
        return a + b + c + d
    
    spec = inspectutils.GetFullArgSpec(func_with_kwonly)
    
    # Check that keyword-only args are properly identified
    assert spec.args == ['a', 'b']
    assert spec.kwonlyargs == ['c', 'd']
    assert spec.kwonlydefaults == {'d': 10}
    

def test_positional_only_args():
    """Test handling of positional-only arguments (Python 3.8+)."""
    
    # Create a function with positional-only args using exec
    if sys.version_info >= (3, 8):
        exec_globals = {}
        exec("""
def func_with_posonly(a, b, /, c, d=10):
    return a + b + c + d
""", exec_globals)
        func_with_posonly = exec_globals['func_with_posonly']
        
        spec = inspectutils.GetFullArgSpec(func_with_posonly)
        
        # Positional-only args should still appear in args
        assert 'a' in spec.args
        assert 'b' in spec.args
        assert 'c' in spec.args
        assert 'd' in spec.args


def test_complex_signature():
    """Test a function with all types of parameters."""
    
    if sys.version_info >= (3, 8):
        exec_globals = {}
        exec("""
def complex_func(pos1, pos2, /, std1, std2=5, *args, kw1, kw2=10, **kwargs):
    pass
""", exec_globals)
        complex_func = exec_globals['complex_func']
        
        spec = inspectutils.GetFullArgSpec(complex_func)
        
        assert 'pos1' in spec.args
        assert 'pos2' in spec.args  
        assert 'std1' in spec.args
        assert 'std2' in spec.args
        assert spec.varargs == 'args'
        assert 'kw1' in spec.kwonlyargs
        assert 'kw2' in spec.kwonlyargs
        assert spec.varkw == 'kwargs'
        assert spec.kwonlydefaults == {'kw2': 10}


def test_namedtuple_subclass_with_new():
    """Test namedtuple subclass that overrides __new__."""
    
    Base = collections.namedtuple('Base', ['x', 'y'])
    
    class SubclassWithNew(Base):
        def __new__(cls, x, y, z=10):
            # Only pass x and y to the base namedtuple
            instance = super().__new__(cls, x, y)
            instance.z = z
            return instance
    
    spec = inspectutils.GetFullArgSpec(SubclassWithNew)
    
    # This is interesting - what args does it detect?
    # The base namedtuple has ['x', 'y'], but __new__ has ['x', 'y', 'z']
    print(f"SubclassWithNew args: {spec.args}")
    print(f"SubclassWithNew defaults: {spec.defaults}")


def test_class_with_metaclass():
    """Test class with custom metaclass."""
    
    class Meta(type):
        def __call__(cls, *args, **kwargs):
            return super().__call__(*args, **kwargs)
    
    class ClassWithMeta(metaclass=Meta):
        def __init__(self, x, y=5):
            self.x = x
            self.y = y
    
    spec = inspectutils.GetFullArgSpec(ClassWithMeta)
    
    # Should still get the __init__ args
    assert 'x' in spec.args
    assert 'y' in spec.args
    assert spec.defaults == (5,)


def test_callable_object():
    """Test object with __call__ method."""
    
    class CallableObject:
        def __call__(self, x, y=10):
            return x + y
    
    obj = CallableObject()
    spec = inspectutils.GetFullArgSpec(obj)
    
    # Should get the __call__ args (without self)
    assert spec.args == ['x', 'y'] or spec.args == ['self', 'x', 'y']
    if 'self' not in spec.args:
        assert spec.defaults == (10,)


def test_property_decorator():
    """Test property decorated methods."""
    
    class WithProperty:
        @property
        def value(self):
            return 42
    
    # Properties are not callable in the usual sense
    prop = WithProperty.value
    
    try:
        spec = inspectutils.GetFullArgSpec(prop)
        # If it doesn't raise, check what it returns
        print(f"Property spec: args={spec.args}, defaults={spec.defaults}")
    except TypeError:
        # Expected for properties
        pass


def test_staticmethod_classmethod():
    """Test static and class methods."""
    
    class WithMethods:
        @staticmethod
        def static_method(x, y=5):
            return x + y
        
        @classmethod
        def class_method(cls, x, y=10):
            return x + y
    
    # Test staticmethod
    spec_static = inspectutils.GetFullArgSpec(WithMethods.static_method)
    assert 'x' in spec_static.args
    assert 'y' in spec_static.args
    
    # Test classmethod  
    spec_class = inspectutils.GetFullArgSpec(WithMethods.class_method)
    # Should have cls or not depending on Python version
    assert 'x' in spec_class.args
    assert 'y' in spec_class.args


def test_slots_class():
    """Test class with __slots__."""
    
    class SlotsClass:
        __slots__ = ['x', 'y']
        
        def __init__(self, x, y):
            self.x = x
            self.y = y
    
    spec = inspectutils.GetFullArgSpec(SlotsClass)
    
    assert 'x' in spec.args
    assert 'y' in spec.args


def test_builtin_subclass():
    """Test subclass of builtin type."""
    
    class MyList(list):
        def __init__(self, items, name="unnamed"):
            super().__init__(items)
            self.name = name
    
    spec = inspectutils.GetFullArgSpec(MyList)
    
    # Should get our __init__ args
    assert 'items' in spec.args
    assert 'name' in spec.args
    assert spec.defaults == ("unnamed",)


def test_info_with_large_object():
    """Test Info with very large objects."""
    
    # Create a large list
    large_list = list(range(10000))
    info = inspectutils.Info(large_list)
    
    # Should handle large objects gracefully
    assert info['type_name'] == 'list'
    assert info.get('length') == '10000'


def test_info_with_recursive_structure():
    """Test Info with recursive data structure."""
    
    # Create a recursive list
    recursive_list = []
    recursive_list.append(recursive_list)
    
    info = inspectutils.Info(recursive_list)
    
    # Should handle recursive structures without hanging
    assert info['type_name'] == 'list'
    assert info.get('length') == '1'


def test_isnamedtuple_with_tuple_subclass():
    """Test IsNamedTuple with tuple subclass that has _fields."""
    
    class TupleWithFields(tuple):
        _fields = ('a', 'b')
    
    t = TupleWithFields([1, 2])
    
    result = inspectutils.IsNamedTuple(t)
    
    # Has _fields and is tuple, so should return True
    assert result is True
    
    # But it's not actually a namedtuple
    assert not hasattr(t, '_asdict')
    assert not hasattr(t, '_replace')


def test_getfullargspec_with_wrapped_function():
    """Test GetFullArgSpec with functools.wraps."""
    
    import functools
    
    def original(x, y=10):
        return x + y
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    
    wrapped = decorator(original)
    
    spec = inspectutils.GetFullArgSpec(wrapped)
    
    # Should follow the wrapper chain and get original's signature
    # Based on the code, Py3GetFullArgSpec uses follow_wrapper_chains=True
    assert 'x' in spec.args
    assert 'y' in spec.args
    assert spec.defaults == (10,)


def test_getfullargspec_with_partial():
    """Test GetFullArgSpec with functools.partial."""
    
    import functools
    
    def func(a, b, c=10):
        return a + b + c
    
    partial_func = functools.partial(func, 1)
    
    try:
        spec = inspectutils.GetFullArgSpec(partial_func)
        # Partial functions might have modified signatures
        print(f"Partial spec: args={spec.args}, defaults={spec.defaults}")
    except TypeError:
        # Might not be inspectable
        pass


def test_multiple_defaults_kwonly():
    """Test function with multiple defaults and keyword-only args."""
    
    def func(a, b=1, c=2, d=3, *, e, f=4, g=5):
        pass
    
    spec = inspectutils.GetFullArgSpec(func)
    
    assert spec.args == ['a', 'b', 'c', 'd']
    assert spec.defaults == (1, 2, 3)
    assert set(spec.kwonlyargs) == {'e', 'f', 'g'}
    assert spec.kwonlydefaults == {'f': 4, 'g': 5}


def test_annotations_with_all_param_types():
    """Test annotations on all parameter types."""
    
    if sys.version_info >= (3, 8):
        exec_globals = {}
        exec("""
def annotated_func(
    pos1: int, 
    pos2: str, 
    /, 
    std1: float, 
    std2: bool = True,
    *args: int,
    kw1: list,
    kw2: dict = None,
    **kwargs: str
) -> tuple:
    pass
""", exec_globals)
        annotated_func = exec_globals['annotated_func']
        
        spec = inspectutils.GetFullArgSpec(annotated_func)
        
        # Check annotations are preserved
        assert 'pos1' in spec.annotations
        assert 'pos2' in spec.annotations
        assert 'std1' in spec.annotations
        assert 'std2' in spec.annotations
        assert 'args' in spec.annotations
        assert 'kw1' in spec.annotations
        assert 'kw2' in spec.annotations
        assert 'kwargs' in spec.annotations
        assert 'return' in spec.annotations


def test_empty_function():
    """Test completely empty function."""
    
    def empty():
        pass
    
    spec = inspectutils.GetFullArgSpec(empty)
    
    assert spec.args == []
    assert spec.defaults is None or spec.defaults == ()
    assert spec.varargs is None
    assert spec.varkw is None
    assert spec.kwonlyargs == []
    assert spec.kwonlydefaults == {} or spec.kwonlydefaults is None


def test_lambda_with_defaults():
    """Test lambda with default arguments."""
    
    f = lambda x, y=10, z=20: x + y + z
    
    spec = inspectutils.GetFullArgSpec(f)
    
    assert spec.args == ['x', 'y', 'z']
    assert spec.defaults == (10, 20)


if __name__ == '__main__':
    # Run individual tests
    test_kwonly_args_handling()
    test_positional_only_args()
    test_complex_signature()
    test_namedtuple_subclass_with_new()
    test_class_with_metaclass()
    test_callable_object()
    test_property_decorator()
    test_staticmethod_classmethod()
    test_slots_class()
    test_builtin_subclass()
    test_info_with_large_object()
    test_info_with_recursive_structure()
    test_isnamedtuple_with_tuple_subclass()
    test_getfullargspec_with_wrapped_function()
    test_getfullargspec_with_partial()
    test_multiple_defaults_kwonly()
    test_annotations_with_all_param_types()
    test_empty_function()
    test_lambda_with_defaults()
    
    print("\nAll edge case tests completed!")