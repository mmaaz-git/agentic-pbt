#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

try:
    import pyramid.request
    print("Success - pyramid.request module found")
    print(f"Module location: {pyramid.request.__file__}")
except ImportError as e:
    print(f"Error: {e}")