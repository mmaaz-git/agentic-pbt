#!/usr/bin/env python3
"""Focused bug hunting for fire.inspectutils using property-based testing."""

import collections
import inspect
import sys
import traceback
from types import ModuleType

# Add fire_env to path  
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')
import fire.inspectutils as inspectutils

print("Focused bug hunting for fire.inspectutils...")

# Bug Hunt 1: Check for edge cases in IsNamedTuple
print("\n1. Testing IsNamedTuple edge cases...")

# Create a fake tuple with _fields attribute (but not a real namedtuple)
class FakeTuple(tuple):
    _fields = ['x', 'y']

fake_instance = FakeTuple([1, 2])
result = inspectutils.IsNamedTuple(fake_instance)
print(f"  FakeTuple with _fields: {result}")
# This could be a false positive - let's verify

# Create actual namedtuple for comparison
RealNT = collections.namedtuple('RealNT', ['x', 'y'])
real_instance = RealNT(1, 2)
real_result = inspectutils.IsNamedTuple(real_instance)
print(f"  Real namedtuple: {real_result}")

# Test with empty _fields
class EmptyFieldsTuple(tuple):
    _fields = []

empty_fields_instance = EmptyFieldsTuple()
empty_result = inspectutils.IsNamedTuple(empty_fields_instance)
print(f"  Tuple with empty _fields: {empty_result}")

# Test with None _fields
class NoneFieldsTuple(tuple):
    _fields = None

none_fields_instance = NoneFieldsTuple()
none_result = inspectutils.IsNamedTuple(none_fields_instance) 
print(f"  Tuple with None _fields: {none_result}")


# Bug Hunt 2: GetFullArgSpec with builtin edge cases
print("\n2. Testing GetFullArgSpec with builtins...")

# Test with module attribute that's a builtin
builtin_method = str.upper
try:
    spec = inspectutils.GetFullArgSpec(builtin_method)
    print(f"  str.upper spec: args={spec.args}, varargs={spec.varargs}, varkw={spec.varkw}")
    
    # According to the code, builtins with __self__ that's not a module should skip first arg
    # Let's check if this is handled correctly
    bound_builtin = "test".upper
    bound_spec = inspectutils.GetFullArgSpec(bound_builtin)
    print(f"  'test'.upper spec: args={bound_spec.args}, varargs={bound_spec.varargs}, varkw={bound_spec.varkw}")
    
except Exception as e:
    print(f"  Exception: {e}")


# Bug Hunt 3: GetFullArgSpec with classes that have weird __init__
print("\n3. Testing GetFullArgSpec with special classes...")

# Class with __init__ that takes no args besides self
class NoArgsInit:
    def __init__(self):
        pass

try:
    spec = inspectutils.GetFullArgSpec(NoArgsInit)
    print(f"  NoArgsInit: args={spec.args}")
    # Should be empty list since self is skipped
    assert spec.args == [], f"Expected empty args, got {spec.args}"
except Exception as e:
    print(f"  Exception: {e}")

# Class with property that shadows a method
class PropertyShadow:
    @property
    def method(self):
        return "property"
    
try:
    spec = inspectutils.GetFullArgSpec(PropertyShadow)
    print(f"  PropertyShadow: args={spec.args}")
except Exception as e:
    print(f"  Exception: {e}")


# Bug Hunt 4: Info function with objects that have weird __str__
print("\n4. Testing Info with objects with unusual __str__...")

class BadStr:
    def __str__(self):
        raise ValueError("Cannot convert to string!")

try:
    bad_obj = BadStr()
    info = inspectutils.Info(bad_obj)
    print(f"  BadStr info: string_form={info.get('string_form', 'MISSING')}")
    # This should fail because Info calls str(component)!
except Exception as e:
    print(f"  ✗ BUG FOUND: Info crashes with bad __str__: {e}")
    

# Bug Hunt 5: GetFileAndLine with special objects
print("\n5. Testing GetFileAndLine edge cases...")

# Test with lambda
lambda_func = lambda x: x + 1
filename, lineno = inspectutils.GetFileAndLine(lambda_func)
print(f"  Lambda: file={filename}, line={lineno}")

# Test with built-in type
filename, lineno = inspectutils.GetFileAndLine(int)
print(f"  int type: file={filename}, line={lineno}")
assert filename is None and lineno is None, "Built-in should return (None, None)"


# Bug Hunt 6: Py3GetFullArgSpec edge cases
print("\n6. Testing Py3GetFullArgSpec directly...")

# Test with object that has no callable signature
class NotCallable:
    pass

not_callable = NotCallable()
try:
    spec = inspectutils.Py3GetFullArgSpec(not_callable)
    print(f"  NotCallable spec: {spec}")
except TypeError as e:
    print(f"  Expected TypeError: {e}")
    

# Bug Hunt 7: _GetArgSpecInfo edge cases  
print("\n7. Testing _GetArgSpecInfo logic...")

# Test with bound method where __self__ is a module
import os
# os.path.join is actually from posixpath module
if hasattr(os.path, 'join'):
    fn, skip = inspectutils._GetArgSpecInfo(os.path.join)
    print(f"  os.path.join: skip_arg={skip}")


# Bug Hunt 8: FullArgSpec with None defaults becoming empty tuple
print("\n8. Testing FullArgSpec None handling...")

# According to the code, None defaults should become ()
spec1 = inspectutils.FullArgSpec(defaults=None)
assert spec1.defaults == (), f"Expected (), got {spec1.defaults}"

spec2 = inspectutils.FullArgSpec(kwonlydefaults=None)  
assert spec2.kwonlydefaults == {}, f"Expected {{}}, got {spec2.kwonlydefaults}"

print("  ✓ FullArgSpec correctly converts None to empty collections")


# Bug Hunt 9: Double defaults assignment in Py3GetFullArgSpec
print("\n9. Checking for duplicate code in Py3GetFullArgSpec...")

# Looking at lines 119-121 in the source:
# defaults = ()
# annotations = {}
# defaults = ()  # <-- This is duplicated!

print("  Note: Line 121 has duplicate 'defaults = ()' assignment")
print("  This is dead code but not a functional bug")


print("\n" + "="*60)
print("Bug hunting complete!")
print("\nPotential issues found:")
print("1. IsNamedTuple can have false positives with fake tuples that have _fields")  
print("2. Info() will crash if object's __str__ method raises an exception")
print("3. Minor: Duplicate line of code in Py3GetFullArgSpec (line 121)")