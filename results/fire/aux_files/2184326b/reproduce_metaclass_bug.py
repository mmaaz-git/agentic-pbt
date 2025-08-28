#!/usr/bin/env python3
"""Minimal reproduction of the metaclass bug in fire.inspectutils."""

import sys
import inspect
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')
import fire.inspectutils as inspectutils


# Minimal test case
class MetaWithCall(type):
    """Metaclass that overrides __call__."""
    def __call__(cls, *args, **kwargs):
        # This __call__ method interferes with GetFullArgSpec
        return super().__call__(*args, **kwargs)


class BuggyClass(metaclass=MetaWithCall):
    """Class with a metaclass that overrides __call__."""
    def __init__(self, x, y=5):
        self.x = x
        self.y = y


class NormalClass:
    """Normal class without metaclass for comparison."""
    def __init__(self, x, y=5):
        self.x = x
        self.y = y


def main():
    print("Reproducing the bug:")
    print("-" * 40)
    
    # Test normal class
    print("NormalClass (without metaclass):")
    normal_spec = inspectutils.GetFullArgSpec(NormalClass)
    print(f"  args: {normal_spec.args}")
    print(f"  defaults: {normal_spec.defaults}")
    print(f"  ✓ Correctly extracted __init__ parameters")
    
    print()
    
    # Test buggy class
    print("BuggyClass (with metaclass that overrides __call__):")
    buggy_spec = inspectutils.GetFullArgSpec(BuggyClass)
    print(f"  args: {buggy_spec.args}")
    print(f"  defaults: {buggy_spec.defaults}")
    print(f"  varargs: {buggy_spec.varargs}")
    print(f"  varkw: {buggy_spec.varkw}")
    
    if buggy_spec.args != ['x', 'y']:
        print(f"  ✗ BUG: Expected args=['x', 'y'], got args={buggy_spec.args}")
        print(f"  ✗ The function returns generic *args/**kwargs instead of __init__ params")
    
    print()
    print("Root cause analysis:")
    print("-" * 40)
    
    # Let's trace what's happening
    print("1. Check if BuggyClass is callable:", callable(BuggyClass))
    print("2. Check if it's a class:", inspect.isclass(BuggyClass))
    
    # The issue is likely in how GetFullArgSpec handles classes with metaclasses
    # Let's check what it's actually inspecting
    fn, skip_arg = inspectutils._GetArgSpecInfo(BuggyClass)
    print(f"3. _GetArgSpecInfo returns: fn={fn}, skip_arg={skip_arg}")
    
    # Let's check what Python's inspect module sees
    print("\n4. What Python's inspect.signature sees:")
    try:
        sig = inspect.signature(BuggyClass)
        print(f"   signature: {sig}")
        print(f"   parameters: {list(sig.parameters.keys())}")
    except Exception as e:
        print(f"   Error: {e}")
    
    print("\n5. Checking BuggyClass.__init__ directly:")
    init_spec = inspectutils.GetFullArgSpec(BuggyClass.__init__)
    print(f"   args: {init_spec.args}")
    print(f"   defaults: {init_spec.defaults}")
    
    return buggy_spec.args != ['x', 'y']


if __name__ == '__main__':
    has_bug = main()
    
    if has_bug:
        print("\n" + "=" * 50)
        print("BUG CONFIRMED:")
        print("GetFullArgSpec fails to extract __init__ parameters")
        print("from classes with metaclasses that override __call__")
        print("=" * 50)