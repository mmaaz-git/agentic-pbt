#!/usr/bin/env python3
"""Simple test runner that doesn't require external dependencies."""

import sys
import traceback
import functools
import inspect
import json

# Add current directory to path
sys.path.insert(0, '.')
import pyramid_decorator

print("="*60)
print("TESTING pyramid_decorator")
print("="*60)

# Test 1: Test reify - should only call function once
print("\n[TEST 1] reify decorator")
call_count = 0

class TestReify:
    @pyramid_decorator.reify
    def expensive_computation(self):
        global call_count
        call_count += 1
        return 42

obj = TestReify()
result1 = obj.expensive_computation
result2 = obj.expensive_computation
result3 = obj.expensive_computation

if call_count == 1:
    print("✓ PASSED: reify only calls function once")
else:
    print(f"✗ FAILED: reify called function {call_count} times instead of 1")

# Test 2: cached_property 
print("\n[TEST 2] cached_property")
call_count2 = 0

class TestCached:
    @pyramid_decorator.cached_property
    def value(self):
        global call_count2
        call_count2 += 1
        return "cached"

obj2 = TestCached()
r1 = obj2.value
r2 = obj2.value

if call_count2 == 1 and r1 == r2 == "cached":
    print("✓ PASSED: cached_property caches correctly")
else:
    print(f"✗ FAILED: cached_property called {call_count2} times")

# Test 3: compose order
print("\n[TEST 3] compose decorator order")

def add_one(func):
    @functools.wraps(func)
    def wrapper(x):
        return func(x) + 1
    return wrapper

def multiply_two(func):
    @functools.wraps(func)
    def wrapper(x):
        return func(x) * 2
    return wrapper

def base(x):
    return x

# compose(add_one, multiply_two)(base) should be add_one(multiply_two(base))
composed = pyramid_decorator.compose(add_one, multiply_two)(base)
manual = add_one(multiply_two(base))

test_val = 5
if composed(test_val) == manual(test_val):
    print(f"✓ PASSED: compose order correct ({composed(test_val)} == {manual(test_val)})")
else:
    print(f"✗ FAILED: compose order wrong ({composed(test_val)} != {manual(test_val)})")

# Test 4: view_config JSON renderer
print("\n[TEST 4] view_config JSON renderer")

@pyramid_decorator.view_config(renderer='json')
def json_view():
    return {"key": "value", "number": 123}

result = json_view()
if isinstance(result, str):
    try:
        parsed = json.loads(result)
        if parsed == {"key": "value", "number": 123}:
            print("✓ PASSED: JSON renderer works")
        else:
            print(f"✗ FAILED: JSON data mismatch: {parsed}")
    except:
        print(f"✗ FAILED: Invalid JSON: {result}")
else:
    print(f"✗ FAILED: Result not a string: {type(result)}")

# Test 5: validate_arguments
print("\n[TEST 5] validate_arguments")

@pyramid_decorator.validate_arguments(x=lambda x: x > 0)
def positive_only(x):
    return x * 2

try:
    result = positive_only(5)
    if result == 10:
        print("✓ PASSED: Valid argument accepted")
    else:
        print(f"✗ FAILED: Wrong result: {result}")
except:
    print("✗ FAILED: Valid argument rejected")

try:
    result = positive_only(-5)
    print(f"✗ FAILED: Invalid argument not rejected: {result}")
except ValueError as e:
    if "Invalid value for x" in str(e):
        print("✓ PASSED: Invalid argument rejected correctly")
    else:
        print(f"✗ FAILED: Wrong error message: {e}")

# Test 6: preserve_signature
print("\n[TEST 6] preserve_signature")

def original(a, b, c=3):
    return a + b + c

def wrapper(*args, **kwargs):
    return original(*args, **kwargs) * 2

preserved = pyramid_decorator.preserve_signature(original)(wrapper)

orig_sig = inspect.signature(original)
pres_sig = inspect.signature(preserved)

if str(orig_sig) == str(pres_sig):
    print(f"✓ PASSED: Signature preserved: {pres_sig}")
else:
    print(f"✗ FAILED: Signature not preserved: {orig_sig} != {pres_sig}")

# Test 7: Decorator callbacks
print("\n[TEST 7] Decorator class callbacks")

callback_executed = []

dec = pyramid_decorator.Decorator(test_setting="value")
dec.add_callback(lambda w, a, k: callback_executed.append(1))
dec.add_callback(lambda w, a, k: callback_executed.append(2))

@dec
def test_func():
    return "result"

result = test_func()

if callback_executed == [1, 2] and result == "result":
    print("✓ PASSED: Callbacks executed in order")
else:
    print(f"✗ FAILED: Callbacks: {callback_executed}, Result: {result}")

# Test 8: Test potential bug in view_config with existing __view_settings__
print("\n[TEST 8] view_config attribute mutation bug")

def func1():
    return "func1"

def func2():
    return "func2"

# Apply decorator to func1
decorated1 = pyramid_decorator.view_config(route='route1')(func1)

# Apply decorator to func2
decorated2 = pyramid_decorator.view_config(route='route2')(func2)

# Check if func1's settings were affected
if hasattr(func1, '__view_settings__'):
    print(f"✗ BUG FOUND: Original function func1 was mutated with __view_settings__")
    print(f"  func1.__view_settings__ = {func1.__view_settings__}")
else:
    print("✓ PASSED: Original functions not mutated")

# Test 9: Test subscriber decorator
print("\n[TEST 9] subscriber decorator")

@pyramid_decorator.subscriber('event1', 'event2')
def handler(event):
    return f"Handled {event}"

if hasattr(handler, '__subscriber_interfaces__'):
    if handler.__subscriber_interfaces__ == ('event1', 'event2'):
        print("✓ PASSED: Subscriber interfaces stored correctly")
    else:
        print(f"✗ FAILED: Wrong interfaces: {handler.__subscriber_interfaces__}")
else:
    print("✗ FAILED: No __subscriber_interfaces__ attribute")

# Test 10: Edge case - empty compose
print("\n[TEST 10] compose with no decorators")

@pyramid_decorator.compose()
def unchanged(x):
    return x * 3

if unchanged(4) == 12:
    print("✓ PASSED: Empty compose preserves function")
else:
    print(f"✗ FAILED: Empty compose changed behavior: {unchanged(4)}")

print("\n" + "="*60)
print("Testing complete")
print("="*60)