#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')

import numpy as np
import awkward as ak
from awkward.contents import IndexedArray, IndexedOptionArray, NumpyArray
from awkward.index import Index64

def test_both_indexed_types():
    """Compare IndexedArray and IndexedOptionArray with out-of-bounds indices."""
    
    # Create content of size 10 for clarity
    content = NumpyArray(np.arange(10, dtype=np.float64))
    
    # Test various index patterns
    test_cases = [
        ("Valid indices", [0, 5, 9]),
        ("Negative index (IndexedOption should treat as None)", [-1, 0, 5]),
        ("Out of bounds positive", [0, 10, 5]),  # 10 is out of bounds
        ("Way out of bounds", [0, 100, 5]),      # 100 is way out of bounds
    ]
    
    for desc, indices in test_cases:
        print(f"\n{'='*60}")
        print(f"Test case: {desc}")
        print(f"Indices: {indices}")
        print(f"Content size: {len(content)}")
        
        # Test IndexedArray
        print("\nIndexedArray:")
        try:
            index = Index64(np.array(indices, dtype=np.int64))
            arr = IndexedArray(index, content)
            print(f"  Created successfully, length: {len(arr)}")
            
            # Try to access each element
            for i in range(len(arr)):
                try:
                    value = arr[i]
                    print(f"  arr[{i}] = {value}")
                except Exception as e:
                    print(f"  arr[{i}] raised {type(e).__name__}: {e}")
        except Exception as e:
            print(f"  Creation failed with {type(e).__name__}: {e}")
        
        # Test IndexedOptionArray
        print("\nIndexedOptionArray:")
        try:
            index = Index64(np.array(indices, dtype=np.int64))
            arr = IndexedOptionArray(index, content)
            print(f"  Created successfully, length: {len(arr)}")
            
            # Try to access each element
            for i in range(len(arr)):
                try:
                    value = arr[i]
                    if value is None:
                        print(f"  arr[{i}] = None")
                    else:
                        print(f"  arr[{i}] = {value}")
                except Exception as e:
                    print(f"  arr[{i}] raised {type(e).__name__}: {e}")
        except Exception as e:
            print(f"  Creation failed with {type(e).__name__}: {e}")

def check_documentation():
    """Check what the documentation says about bounds checking."""
    print("\n" + "="*60)
    print("Documentation check:")
    print("\nIndexedArray docstring excerpt:")
    if IndexedArray.__doc__:
        lines = IndexedArray.__doc__.split('\n')[:10]
        for line in lines:
            if line.strip():
                print(f"  {line.strip()}")
    
    print("\nIndexedOptionArray docstring excerpt:")
    if IndexedOptionArray.__doc__:
        lines = IndexedOptionArray.__doc__.split('\n')[:10]
        for line in lines:
            if line.strip():
                print(f"  {line.strip()}")

if __name__ == "__main__":
    test_both_indexed_types()
    check_documentation()