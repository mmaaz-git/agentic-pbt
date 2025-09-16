"""Test edge cases for potential bugs."""

import fire.value_types as vt
from hypothesis import given, strategies as st
import pytest

# Test edge case: What happens with recursive dicts in IsSimpleGroup?
def test_recursive_dict():
    """Test IsSimpleGroup with recursive dict structure."""
    d = {}
    d['self'] = d  # Create a self-referential dict
    
    # This could potentially cause infinite recursion
    try:
        result = vt.IsSimpleGroup(d)
        print(f"Recursive dict: IsSimpleGroup returned {result}")
    except RecursionError as e:
        print(f"BUG: Recursive dict causes RecursionError in IsSimpleGroup")
        raise

# Test with nested structures
def test_deeply_nested():
    """Test with deeply nested dict/list structures."""
    # Create a deeply nested structure
    nested = {"a": {"b": {"c": [1, 2, {"d": [3, 4, {"e": 5}]}]}}}
    
    result = vt.IsSimpleGroup(nested)
    print(f"Deeply nested dict: IsSimpleGroup = {result}")
    
    # What about a dict containing objects?
    class CustomObj:
        pass
    
    mixed = {"obj": CustomObj(), "value": 42}
    result = vt.IsSimpleGroup(mixed)
    print(f"Dict with object: IsSimpleGroup = {result}")
    assert result == False, "Dict with non-value object should not be simple"

# Test classification edge cases
def test_classification_edge_cases():
    """Test edge cases in component classification."""
    
    # What about property objects?
    class WithProperty:
        @property
        def prop(self):
            return 42
    
    obj = WithProperty()
    print(f"Property: IsCommand={vt.IsCommand(obj.prop)}, IsValue={vt.IsValue(obj.prop)}")
    
    # What about classmethods and staticmethods?
    class WithMethods:
        @classmethod
        def cls_method(cls):
            pass
        
        @staticmethod
        def static_method():
            pass
    
    print(f"Classmethod: IsCommand={vt.IsCommand(WithMethods.cls_method)}")
    print(f"Staticmethod: IsCommand={vt.IsCommand(WithMethods.static_method)}")
    
    # What about callable objects?
    class Callable:
        def __call__(self):
            pass
    
    callable_obj = Callable()
    print(f"Callable object: IsCommand={vt.IsCommand(callable_obj)}")
    print(f"Callable object: IsValue={vt.IsValue(callable_obj)}")
    print(f"Callable object: IsGroup={vt.IsGroup(callable_obj)}")

if __name__ == "__main__":
    print("Testing recursive dict...")
    test_recursive_dict()
    print("\nTesting deeply nested structures...")
    test_deeply_nested()
    print("\nTesting classification edge cases...")
    test_classification_edge_cases()