#!/usr/bin/env python3
"""Directly test pyramid_decorator for bugs."""

import sys
sys.path.insert(0, '.')

# Import the module
exec(open('pyramid_decorator.py').read())

print("Testing pyramid_decorator for bugs...")
print("="*60)

# Bug Test 1: view_config mutates the original function
print("\n[BUG TEST 1] view_config function mutation")

def original_func():
    """Original function"""
    return "test"

# Store original state
had_attr_before = hasattr(original_func, '__view_settings__')

# Apply decorator
decorated = view_config(route='test')(original_func)

# Check if original was mutated
if hasattr(original_func, '__view_settings__') and not had_attr_before:
    print("✗ BUG FOUND: view_config mutates the original function!")
    print(f"  The original function now has __view_settings__: {original_func.__view_settings__}")
    print("  This is a bug because decorators should not modify the original function.")
    
    # Create bug reproduction
    bug_repro = '''
# BUG: view_config decorator mutates the original function

def my_function():
    return "hello"

# Before decoration
print(hasattr(my_function, '__view_settings__'))  # False

# Apply decorator
from pyramid_decorator import view_config
decorated = view_config(route='test')(my_function)

# After decoration - original function is mutated!
print(hasattr(my_function, '__view_settings__'))  # True - BUG!
print(my_function.__view_settings__)  # [{'route': 'test'}]
'''
    print("\nReproduction code:")
    print(bug_repro)
else:
    print("✓ No mutation bug found")

# Bug Test 2: MethodDecorator with None func
print("\n[BUG TEST 2] MethodDecorator with parameters")

try:
    # This should work according to the docstring
    md = MethodDecorator(option='value')
    
    # Now decorate a function
    @md
    def method(self):
        return "test"
    
    # Try to use it
    class TestClass:
        decorated_method = method
    
    obj = TestClass()
    # This will likely fail because MethodDecorator's __call__ 
    # expects self.func to be set but it's None when used with params
    result = obj.decorated_method()
    print("✓ MethodDecorator works with parameters")
    
except Exception as e:
    print(f"✗ BUG FOUND: MethodDecorator fails with parameters")
    print(f"  Error: {e}")
    print("  The __call__ method tries to call self.func when it's None")

# Bug Test 3: preserve_signature with no annotations
print("\n[BUG TEST 3] preserve_signature with functions lacking annotations")

def no_annotations(x, y):
    return x + y

def wrapper(*args, **kwargs):
    return no_annotations(*args, **kwargs)

try:
    preserved = preserve_signature(no_annotations)(wrapper)
    # This will fail if no_annotations doesn't have __annotations__
    print("✓ preserve_signature handles functions without annotations")
except AttributeError as e:
    print(f"✗ BUG FOUND: preserve_signature fails on functions without annotations")
    print(f"  Error: {e}")
    print("  Functions without type hints don't have __annotations__ attribute")

# Bug Test 4: validate_arguments with keyword-only arguments
print("\n[BUG TEST 4] validate_arguments with keyword-only arguments")

@validate_arguments(x=lambda x: x > 0)
def func_with_kwonly(*, x):
    return x * 2

try:
    result = func_with_kwonly(x=5)
    print("✓ validate_arguments works with keyword-only arguments")
except Exception as e:
    print(f"✗ Potential issue with keyword-only arguments: {e}")

# Bug Test 5: Decorator with JSON response on non-serializable objects
print("\n[BUG TEST 5] Decorator JSON response with non-serializable data")

import json

dec = Decorator(json_response=True)

@dec
def returns_set():
    return {1, 2, 3}  # Sets are not JSON serializable

try:
    result = returns_set()
    print(f"✓ Handled non-serializable: {result}")
except TypeError as e:
    print(f"✗ BUG FOUND: Decorator crashes on non-JSON-serializable return values")
    print(f"  Error: {e}")
    print("  The decorator should handle or document this limitation")

# Bug Test 6: view_config double JSON encoding
print("\n[BUG TEST 6] view_config double JSON encoding")

@view_config(renderer='json')
def already_json():
    return '{"already": "json"}'  # Already a JSON string

result = already_json()
print(f"Result: {result}")
print(f"Result type: {type(result)}")

# Try to parse it
try:
    parsed = json.loads(result)
    if isinstance(parsed, str):
        # Double encoded!
        print("✗ BUG FOUND: view_config double-encodes JSON strings")
        print(f"  Expected dict, got string: {parsed}")
    else:
        print("✓ JSON encoding works correctly")
except:
    print("✗ BUG FOUND: Invalid JSON produced")

print("\n" + "="*60)
print("Bug hunting complete!")

# Let's also check for the annotation bug more carefully
print("\n[DETAILED CHECK] preserve_signature annotation handling")

def func_without_annotations(a, b):
    return a + b

print(f"Has __annotations__: {hasattr(func_without_annotations, '__annotations__')}")
if not hasattr(func_without_annotations, '__annotations__'):
    print("✗ CONFIRMED BUG: Functions without type hints lack __annotations__")
    print("  preserve_signature will crash on line 182: wrapper.__annotations__ = wrapped.__annotations__")
    
    bug_code = '''
# BUG in preserve_signature - crashes on functions without type annotations

def my_function(x, y):  # No type hints
    return x + y

def my_wrapper(*args, **kwargs):
    return my_function(*args, **kwargs)

# This will crash with AttributeError
from pyramid_decorator import preserve_signature
preserved = preserve_signature(my_function)(my_wrapper)
# AttributeError: 'function' object has no attribute '__annotations__'
'''
    print("\nBug reproduction:")
    print(bug_code)