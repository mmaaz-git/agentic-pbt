#!/usr/bin/env python3
"""Minimal reproduction of the bug in takes_one_arg function."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

import pyramid.util
import pyramid.viewderivers


def demonstrate_bug():
    """Demonstrate the bug in takes_one_arg when argname is specified."""
    
    print("BUG: takes_one_arg returns True for single-arg functions")
    print("     even when the argument name doesn't match argname\n")
    
    # Function with argument named 'foo' (not 'request')
    def foo_func(foo):
        pass
    
    # This should return False because the argument is 'foo', not 'request'
    result = pyramid.util.takes_one_arg(foo_func, argname='request')
    print(f"takes_one_arg(foo_func, argname='request')")
    print(f"  Function signature: def foo_func(foo)")
    print(f"  Expected: False (argument is 'foo', not 'request')")
    print(f"  Actual: {result}")
    print(f"  BUG: Returns True incorrectly!\n")
    
    # This affects requestonly which should only accept 'request' argument
    result2 = pyramid.viewderivers.requestonly(foo_func)
    print(f"requestonly(foo_func)")
    print(f"  Function signature: def foo_func(foo)")
    print(f"  Expected: False (argument must be named 'request')")
    print(f"  Actual: {result2}")
    print(f"  BUG: Returns True incorrectly!\n")
    
    # The bug allows any single-argument function to pass requestonly
    def xyz_func(xyz):
        pass
    
    result3 = pyramid.viewderivers.requestonly(xyz_func)
    print(f"requestonly(xyz_func)")
    print(f"  Function signature: def xyz_func(xyz)")
    print(f"  Expected: False")
    print(f"  Actual: {result3}")
    print(f"  BUG: Returns True incorrectly!\n")
    
    print("Impact: This bug causes requestonly() to incorrectly identify")
    print("        functions as request-only views when they're not,")
    print("        potentially leading to incorrect view mapping behavior")
    print("        in the Pyramid web framework.")


if __name__ == "__main__":
    demonstrate_bug()