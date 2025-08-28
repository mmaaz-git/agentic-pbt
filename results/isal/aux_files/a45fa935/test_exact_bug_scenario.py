#!/usr/bin/env python3
import sys
import tempfile
import os

# Add the isal environment to the path
sys.path.insert(0, '/root/hypothesis-llm/envs/isal_env/lib/python3.13/site-packages')

import isal.igzip_threaded as igzip_threaded
import isal.igzip as igzip

def test_exact_failing_scenario():
    """Test the exact scenario that was failing in the property test."""
    
    # From the failing test: chunks=[b'\x00', b'\x00\x00\x00\x00'], threads=1
    # The test does: write chunk, if i % 3 == 0: flush, repeat
    
    test_cases = [
        # Test the exact failing case
        ([b'\x00', b'\x00\x00\x00\x00'], [0], "Exact failing case: flush after first chunk"),
        
        # Test variations
        ([b'\x00', b'\x00\x00\x00\x00'], [], "Same data, no flush"),
        ([b'\x00', b'\x00\x00\x00\x00'], [1], "Same data, flush after second chunk"),
        
        # Test with empty chunks
        ([b'', b'\x00'], [0], "Empty then data with flush after empty"),
        ([b'\x00', b''], [0], "Data then empty with flush after data"),
        
        # Test multiple flushes
        ([b'A', b'B', b'C'], [0, 1], "Multiple flushes"),
        ([b'\x00', b'\x00', b'\x00'], [0, 1], "Multiple null bytes with multiple flushes"),
    ]
    
    for chunks, flush_indices, description in test_cases:
        print(f"\nTesting: {description}")
        print(f"Chunks: {chunks}")
        print(f"Flush after indices: {flush_indices}")
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # Write with specified flush pattern
            with igzip_threaded.open(tmp_path, "wb", threads=1) as f:
                for i, chunk in enumerate(chunks):
                    f.write(chunk)
                    if i in flush_indices:
                        print(f"  Flushing after chunk {i}")
                        f.flush()
            
            # Try to read with threaded reader
            try:
                with igzip_threaded.open(tmp_path, "rb") as f:
                    recovered_threaded = f.read()
                print(f"  ✓ Threaded read succeeded")
                expected = b''.join(chunks)
                if recovered_threaded == expected:
                    print(f"    Data matches expected")
                else:
                    print(f"    ERROR: Data mismatch!")
                    print(f"    Expected: {expected}")
                    print(f"    Got: {recovered_threaded}")
            except Exception as e:
                print(f"  ✗ Threaded read failed: {e}")
                
            # Try to read with regular igzip
            try:
                with igzip.open(tmp_path, "rb") as f:
                    recovered_regular = f.read()
                print(f"  ✓ Regular igzip read succeeded")
            except Exception as e:
                print(f"  ✗ Regular igzip read failed: {e}")
                
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

if __name__ == "__main__":
    test_exact_failing_scenario()