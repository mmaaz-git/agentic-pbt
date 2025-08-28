#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

try:
    import pyramid.interfaces
    print('success - treating as module')
    print(f"Module file: {pyramid.interfaces.__file__}")
except ImportError as e:
    print(f"Failed to import: {e}")