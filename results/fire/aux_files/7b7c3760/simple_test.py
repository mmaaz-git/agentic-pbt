#!/usr/bin/env python3
"""Simple property-based test runner for fire.inspectutils."""

import collections
import sys

# Add fire_env to path
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')
import fire.inspectutils as inspectutils

print("Testing fire.inspectutils properties...")

# Test 1: IsNamedTuple with real namedtuples
print("\n1. Testing IsNamedTuple...")
Point = collections.namedtuple('Point', ['x', 'y'])
point_instance = Point(1, 2)

# Instance should be detected as namedtuple
assert inspectutils.IsNamedTuple(point_instance) == True, "Failed: namedtuple instance not detected"

# Class itself should not be detected as namedtuple
assert inspectutils.IsNamedTuple(Point) == False, "Failed: namedtuple class incorrectly detected"

# Regular tuple should not be detected
assert inspectutils.IsNamedTuple((1, 2)) == False, "Failed: regular tuple incorrectly detected"
print("  ✓ IsNamedTuple works correctly")

# Test 2: Info function
print("\n2. Testing Info function...")
info = inspectutils.Info(42)
assert isinstance(info, dict), "Failed: Info didn't return dict"
assert 'type_name' in info, "Failed: type_name not in info"
assert 'string_form' in info, "Failed: string_form not in info"
assert info['string_form'] == '42', f"Failed: string_form mismatch, got {info['string_form']}"
print("  ✓ Info function works correctly")

# Test 3: GetFullArgSpec with simple function
print("\n3. Testing GetFullArgSpec...")
def test_func(a, b=10, *args, **kwargs):
    return a + b

spec = inspectutils.GetFullArgSpec(test_func)
assert spec.args == ['a', 'b'], f"Failed: args mismatch, got {spec.args}"
assert spec.defaults == (10,), f"Failed: defaults mismatch, got {spec.defaults}"
assert spec.varargs == 'args', f"Failed: varargs mismatch, got {spec.varargs}"
assert spec.varkw == 'kwargs', f"Failed: varkw mismatch, got {spec.varkw}"
print("  ✓ GetFullArgSpec works correctly")

# Test 4: GetClassAttrsDict
print("\n4. Testing GetClassAttrsDict...")
class TestClass:
    x = 1
    def method(self):
        pass

attrs = inspectutils.GetClassAttrsDict(TestClass)
assert isinstance(attrs, dict), "Failed: GetClassAttrsDict didn't return dict for class"
assert 'x' in attrs, "Failed: class attribute 'x' not found"
assert 'method' in attrs, "Failed: class method 'method' not found"

# Non-class should return None
assert inspectutils.GetClassAttrsDict(42) is None, "Failed: GetClassAttrsDict didn't return None for non-class"
print("  ✓ GetClassAttrsDict works correctly")

# Test 5: IsCoroutineFunction
print("\n5. Testing IsCoroutineFunction...")
async def async_func():
    return 42

def sync_func():
    return 42

assert inspectutils.IsCoroutineFunction(async_func) == True, "Failed: async function not detected"
assert inspectutils.IsCoroutineFunction(sync_func) == False, "Failed: sync function incorrectly detected as async"
print("  ✓ IsCoroutineFunction works correctly")

# Test 6: FullArgSpec constructor
print("\n6. Testing FullArgSpec constructor...")
spec = inspectutils.FullArgSpec(
    args=['a', 'b'],
    varargs='args',
    varkw='kwargs',
    defaults=(1, 2),
    kwonlyargs=['x'],
    kwonlydefaults={'x': 10},
    annotations={'a': int}
)
assert spec.args == ['a', 'b'], "Failed: FullArgSpec args not set correctly"
assert spec.defaults == (1, 2), "Failed: FullArgSpec defaults not set correctly"
print("  ✓ FullArgSpec constructor works correctly")

print("\n" + "="*60)
print("All basic property tests passed! ✅")
print("\nNow running more comprehensive property-based tests with Hypothesis...")