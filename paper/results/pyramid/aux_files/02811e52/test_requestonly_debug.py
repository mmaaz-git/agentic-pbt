#!/usr/bin/env python3
"""Debug the requestonly function to understand the failures."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st
import pyramid.viewderivers as vd


# Test requestonly function - corrected version
def test_requestonly_basic():
    """Test basic requestonly functionality."""
    
    # Function that takes only 'request' argument
    def request_only_func(request):
        pass
    
    result = vd.requestonly(request_only_func)
    print(f"request_only_func: {result}")
    assert result == True
    
    # Function with wrong argument name
    def wrong_arg_func(req):
        pass
    
    result = vd.requestonly(wrong_arg_func)
    print(f"wrong_arg_func: {result}")
    assert result == False
    
    # Function with multiple args
    def multi_arg_func(context, request):
        pass
    
    result = vd.requestonly(multi_arg_func)
    print(f"multi_arg_func: {result}")
    assert result == False


def test_requestonly_with_class():
    """Test requestonly with classes."""
    
    class RequestOnlyClass:
        def __init__(self, request):
            self.request = request
    
    result = vd.requestonly(RequestOnlyClass)
    print(f"RequestOnlyClass: {result}")
    assert result == True
    
    class ContextRequestClass:
        def __init__(self, context, request):
            self.context = context
            self.request = request
    
    result = vd.requestonly(ContextRequestClass)
    print(f"ContextRequestClass: {result}")
    assert result == False


@given(st.text(min_size=1).filter(lambda x: x.isidentifier()))
def test_requestonly_with_different_arg_names(arg_name):
    """Test that requestonly only accepts 'request' as the argument name."""
    
    # Create a function with the given argument name
    func_code = f"def test_func({arg_name}): pass"
    exec(func_code, globals())
    func = globals()['test_func']
    
    result = vd.requestonly(func)
    
    # Should only be True if arg_name is 'request'
    expected = (arg_name == 'request')
    assert result == expected, f"For arg_name={arg_name}, expected {expected} but got {result}"
    
    # Clean up
    del globals()['test_func']


if __name__ == "__main__":
    print("Testing requestonly function...")
    test_requestonly_basic()
    test_requestonly_with_class()
    test_requestonly_with_different_arg_names()
    print("All tests passed!")