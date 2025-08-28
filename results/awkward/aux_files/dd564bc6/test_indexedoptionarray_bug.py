#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import numpy as np
import awkward as ak
from awkward.contents import IndexedOptionArray, NumpyArray
from awkward.index import Index64

# Minimal reproduction of the bug
def test_indexedoptionarray_out_of_bounds():
    """Test IndexedOptionArray with out-of-bounds index."""
    
    # Create content of size 50
    content = NumpyArray(np.arange(50, dtype=np.float64))
    
    # Create index with value 50 (which is out of bounds for 0-indexed array of size 50)
    indices = [0, 50]  # 50 is out of bounds
    index = Index64(np.array(indices, dtype=np.int64))
    
    # Create IndexedOptionArray
    arr = IndexedOptionArray(index, content)
    
    print(f"Created IndexedOptionArray with length: {len(arr)}")
    print(f"Index values: {index.data}")
    print(f"Content length: {len(content)}")
    
    # Try to access elements
    for i in range(len(arr)):
        try:
            value = arr[i]
            print(f"arr[{i}] = {value}")
        except IndexError as e:
            print(f"arr[{i}] raised IndexError: {e}")
            if i == 1:
                # This is expected behavior for out-of-bounds index
                # But should it be caught at construction time or access time?
                print("\nQuestion: Should IndexedOptionArray validate indices at construction?")
                print("Current behavior: Validation happens at access time")
                print("Alternative: Could validate at construction and raise error early")
                return True
    
    return False

if __name__ == "__main__":
    found_issue = test_indexedoptionarray_out_of_bounds()
    if found_issue:
        print("\n✓ Found behavior worth investigating")
    else:
        print("\n✗ No issue found")