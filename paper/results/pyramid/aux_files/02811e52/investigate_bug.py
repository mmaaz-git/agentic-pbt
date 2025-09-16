#!/usr/bin/env python3
"""Investigate the potential bug in requestonly/takes_one_arg."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

import pyramid.viewderivers as vd
import pyramid.util

# Test the underlying takes_one_arg function
def investigate_takes_one_arg():
    print("Testing takes_one_arg function...")
    
    # Function with 'request' argument
    def request_func(request):
        pass
    
    # Function with different argument name
    def req_func(req):
        pass
    
    # Function with multiple args
    def multi_func(context, request):
        pass
    
    # Test with argname parameter
    result1 = pyramid.util.takes_one_arg(request_func, argname='request')
    print(f"takes_one_arg(request_func, argname='request'): {result1}")
    
    result2 = pyramid.util.takes_one_arg(req_func, argname='request')
    print(f"takes_one_arg(req_func, argname='request'): {result2}")
    
    result3 = pyramid.util.takes_one_arg(req_func, argname='req')
    print(f"takes_one_arg(req_func, argname='req'): {result3}")
    
    # Test without argname parameter
    result4 = pyramid.util.takes_one_arg(request_func)
    print(f"takes_one_arg(request_func): {result4}")
    
    result5 = pyramid.util.takes_one_arg(req_func)
    print(f"takes_one_arg(req_func): {result5}")
    
    result6 = pyramid.util.takes_one_arg(multi_func)
    print(f"takes_one_arg(multi_func): {result6}")
    
    # Now test requestonly which should check for 'request' specifically
    print("\nTesting requestonly function...")
    
    result7 = vd.requestonly(request_func)
    print(f"requestonly(request_func): {result7}")
    
    result8 = vd.requestonly(req_func)
    print(f"requestonly(req_func): {result8}")
    
    result9 = vd.requestonly(multi_func)
    print(f"requestonly(multi_func): {result9}")


if __name__ == "__main__":
    investigate_takes_one_arg()