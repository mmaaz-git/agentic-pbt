#!/usr/bin/env python3
"""Investigate the metaclass handling bug in inspectutils."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')
import fire.inspectutils as inspectutils


def test_metaclass_issue():
    """Reproduce and investigate the metaclass issue."""
    
    class Meta(type):
        def __call__(cls, *args, **kwargs):
            print(f"Meta.__call__ called with args={args}, kwargs={kwargs}")
            return super().__call__(*args, **kwargs)
    
    class ClassWithMeta(metaclass=Meta):
        def __init__(self, x, y=5):
            print(f"ClassWithMeta.__init__ called with x={x}, y={y}")
            self.x = x
            self.y = y
    
    print("Getting FullArgSpec for ClassWithMeta...")
    spec = inspectutils.GetFullArgSpec(ClassWithMeta)
    
    print(f"spec.args: {spec.args}")
    print(f"spec.defaults: {spec.defaults}")
    print(f"spec.varargs: {spec.varargs}")
    print(f"spec.varkw: {spec.varkw}")
    print(f"spec.kwonlyargs: {spec.kwonlyargs}")
    print(f"spec.kwonlydefaults: {spec.kwonlydefaults}")
    
    # What we expect:
    # spec.args should be ['x', 'y'] (from __init__, minus self)
    # spec.defaults should be (5,)
    
    if 'x' not in spec.args or 'y' not in spec.args:
        print("\nBUG FOUND: Class with metaclass doesn't properly extract __init__ args!")
        print(f"Expected args to contain ['x', 'y'], got: {spec.args}")
        return True
    
    return False


def test_regular_class():
    """Test regular class for comparison."""
    
    class RegularClass:
        def __init__(self, x, y=5):
            self.x = x
            self.y = y
    
    print("\nGetting FullArgSpec for RegularClass...")
    spec = inspectutils.GetFullArgSpec(RegularClass)
    
    print(f"spec.args: {spec.args}")
    print(f"spec.defaults: {spec.defaults}")
    

def test_various_metaclasses():
    """Test various metaclass scenarios."""
    
    # Metaclass with __new__
    class MetaWithNew(type):
        def __new__(mcs, name, bases, namespace):
            return super().__new__(mcs, name, bases, namespace)
    
    class ClassWithMetaNew(metaclass=MetaWithNew):
        def __init__(self, a, b=10):
            self.a = a
            self.b = b
    
    print("\nClassWithMetaNew:")
    spec1 = inspectutils.GetFullArgSpec(ClassWithMetaNew)
    print(f"args: {spec1.args}, defaults: {spec1.defaults}")
    
    # Metaclass with __init__
    class MetaWithInit(type):
        def __init__(cls, name, bases, namespace):
            super().__init__(name, bases, namespace)
    
    class ClassWithMetaInit(metaclass=MetaWithInit):
        def __init__(self, c, d=20):
            self.c = c
            self.d = d
    
    print("\nClassWithMetaInit:")
    spec2 = inspectutils.GetFullArgSpec(ClassWithMetaInit)
    print(f"args: {spec2.args}, defaults: {spec2.defaults}")
    
    # Check if any fail
    if 'a' not in spec1.args or 'b' not in spec1.args:
        print(f"BUG: ClassWithMetaNew failed - expected ['a', 'b'], got {spec1.args}")
        return True
    
    if 'c' not in spec2.args or 'd' not in spec2.args:
        print(f"BUG: ClassWithMetaInit failed - expected ['c', 'd'], got {spec2.args}")
        return True
    
    return False


if __name__ == '__main__':
    print("=" * 60)
    print("Testing metaclass handling in inspectutils.GetFullArgSpec")
    print("=" * 60)
    
    bug_found = False
    
    if test_metaclass_issue():
        bug_found = True
    
    test_regular_class()
    
    if test_various_metaclasses():
        bug_found = True
    
    if bug_found:
        print("\n" + "=" * 60)
        print("BUG CONFIRMED: GetFullArgSpec has issues with metaclasses")
        print("=" * 60)