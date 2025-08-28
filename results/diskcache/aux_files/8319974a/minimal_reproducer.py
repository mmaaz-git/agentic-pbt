"""Minimal reproducer for Index equality bug"""

import tempfile
import sys

# Add the diskcache environment to path
sys.path.insert(0, '/root/hypothesis-llm/envs/diskcache_env/lib/python3.13/site-packages')

from diskcache.persistent import Index

# Minimal failing example found by Hypothesis
with tempfile.TemporaryDirectory() as tmpdir:
    index = Index(tmpdir, {'0': 0})
    
    # This should return False, but instead raises TypeError
    try:
        result = (index == None)
        print(f"index == None returned: {result}")
    except TypeError as e:
        print(f"BUG: index == None raised TypeError: {e}")
    
    # Test with integer
    try:
        result = (index == 123)
        print(f"index == 123 returned: {result}")
    except TypeError as e:
        print(f"BUG: index == 123 raised TypeError: {e}")
    
    # Test __ne__ as well
    try:
        result = (index != None)
        print(f"index != None returned: {result}")
    except TypeError as e:
        print(f"BUG: index != None raised TypeError: {e}")
    
    try:
        result = (index != 123)
        print(f"index != 123 returned: {result}")
    except TypeError as e:
        print(f"BUG: index != 123 raised TypeError: {e}")