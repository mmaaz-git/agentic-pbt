"""Test to reproduce Index.__eq__ bug"""

import tempfile
import sys

# Add the diskcache environment to path
sys.path.insert(0, '/root/hypothesis-llm/envs/diskcache_env/lib/python3.13/site-packages')

from diskcache.persistent import Index

def test_index_eq_with_non_mapping():
    """Index.__eq__ fails when comparing with non-mapping types"""
    with tempfile.TemporaryDirectory() as tmpdir:
        index = Index(tmpdir, {'a': 1, 'b': 2})
        
        # This should return False, not raise TypeError
        try:
            result = (index == 123)
            print(f"Comparison with int: {result}")
        except TypeError as e:
            print(f"BUG FOUND: TypeError when comparing Index with int: {e}")
            
        # Try with other non-mapping types
        try:
            result = (index == "string")
            print(f"Comparison with string: {result}")
        except TypeError as e:
            print(f"BUG FOUND: TypeError when comparing Index with string: {e}")
            
        try:
            result = (index == None)
            print(f"Comparison with None: {result}")
        except TypeError as e:
            print(f"BUG FOUND: TypeError when comparing Index with None: {e}")
            
        try:
            result = (index == 3.14)
            print(f"Comparison with float: {result}")
        except TypeError as e:
            print(f"BUG FOUND: TypeError when comparing Index with float: {e}")

if __name__ == "__main__":
    test_index_eq_with_non_mapping()