"""
Detailed test demonstrating the Arrayterator integer indexing bug.
"""

import numpy as np
from numpy.lib import Arrayterator


def test_integer_indexing_dimension_reduction():
    """Test that integer indexing reduces dimensions like regular arrays."""
    
    print("Testing Arrayterator integer indexing behavior\n")
    print("=" * 60)
    
    # Test various array shapes
    test_shapes = [
        (2, 3),
        (3, 4, 5),
        (2, 2, 2, 2),
        (10,),
        (5, 1, 3),
    ]
    
    failures = []
    
    for shape in test_shapes:
        arr = np.arange(np.prod(shape)).reshape(shape)
        iterator = Arrayterator(arr, buf_size=1)
        
        print(f"\nTesting shape {shape}:")
        
        # Test integer indexing at first position
        if len(shape) > 0 and shape[0] > 0:
            arr_indexed = arr[0]
            iter_indexed = iterator[0]
            
            print(f"  arr[0].shape:      {arr_indexed.shape}")
            print(f"  iterator[0].shape: {iter_indexed.shape}")
            
            if arr_indexed.shape != iter_indexed.shape:
                print(f"  ❌ MISMATCH: Shapes differ!")
                failures.append({
                    'shape': shape,
                    'expected': arr_indexed.shape,
                    'got': iter_indexed.shape
                })
            else:
                print(f"  ✓ Shapes match")
        
        # Test multiple integer indices
        if len(shape) >= 2 and all(s > 0 for s in shape[:2]):
            arr_indexed = arr[0, 0]
            iter_indexed = iterator[0, 0]
            
            print(f"  arr[0, 0].shape:      {arr_indexed.shape}")
            print(f"  iterator[0, 0].shape: {iter_indexed.shape}")
            
            if arr_indexed.shape != iter_indexed.shape:
                print(f"  ❌ MISMATCH: Shapes differ for [0, 0]!")
                failures.append({
                    'shape': shape,
                    'index': '[0, 0]',
                    'expected': arr_indexed.shape,
                    'got': iter_indexed.shape
                })
    
    print("\n" + "=" * 60)
    print(f"\nSummary: Found {len(failures)} shape mismatches")
    
    if failures:
        print("\nFailure details:")
        for f in failures:
            print(f"  Array shape {f['shape']}: "
                  f"Expected {f['expected']}, got {f['got']}")
    
    return failures


def test_mixed_indexing():
    """Test mixing integer and slice indexing."""
    
    print("\n\nTesting mixed integer and slice indexing")
    print("=" * 60)
    
    arr = np.arange(24).reshape(4, 3, 2)
    iterator = Arrayterator(arr, buf_size=2)
    
    test_cases = [
        (0, "Integer at position 0"),
        ((0, slice(None)), "Integer at pos 0, slice at pos 1"),
        ((slice(None), 0), "Slice at pos 0, integer at pos 1"),
        ((0, 0), "Two integers"),
        ((0, slice(1, 3)), "Integer and bounded slice"),
    ]
    
    failures = []
    
    for index, description in test_cases:
        arr_indexed = arr[index]
        iter_indexed = iterator[index]
        
        print(f"\n{description} - index: {index}")
        print(f"  arr{index}.shape:      {arr_indexed.shape}")
        print(f"  iterator{index}.shape: {iter_indexed.shape}")
        
        if arr_indexed.shape != iter_indexed.shape:
            print(f"  ❌ MISMATCH!")
            failures.append({
                'index': index,
                'expected': arr_indexed.shape,
                'got': iter_indexed.shape
            })
        else:
            print(f"  ✓ Match")
    
    return failures


if __name__ == "__main__":
    failures1 = test_integer_indexing_dimension_reduction()
    failures2 = test_mixed_indexing()
    
    total_failures = len(failures1) + len(failures2)
    
    print("\n" + "=" * 60)
    print(f"TOTAL FAILURES: {total_failures}")
    
    if total_failures > 0:
        print("\nThis demonstrates a bug in Arrayterator's __getitem__ method:")
        print("Integer indexing should reduce dimensions but doesn't.")