#!/usr/bin/env python3
import sys
import tempfile
import os

# Add the isal environment to the path
sys.path.insert(0, '/root/hypothesis-llm/envs/isal_env/lib/python3.13/site-packages')

import isal.igzip_threaded as igzip_threaded
import isal.igzip as igzip

def test_various_flush_scenarios():
    """Test different data patterns with flush to understand the bug."""
    
    test_cases = [
        ([b'\x00'], "Single null byte before flush"),
        ([b'\x00\x00'], "Two null bytes before flush"),
        ([b'A'], "Single 'A' byte before flush"),
        ([b'Hello'], "Word before flush"),
        ([b''], "Empty data before flush"),
        ([b'\x00' * 100], "100 null bytes before flush"),
        ([b'A' * 100], "100 'A' bytes before flush"),
    ]
    
    for chunks_before_flush, description in test_cases:
        print(f"\nTesting: {description}")
        print(f"Data before flush: {chunks_before_flush}")
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # Write with flush
            with igzip_threaded.open(tmp_path, "wb", threads=1) as f:
                for chunk in chunks_before_flush:
                    f.write(chunk)
                f.flush()
                f.write(b'After flush')
            
            # Try to read with threaded reader
            try:
                with igzip_threaded.open(tmp_path, "rb") as f:
                    recovered_threaded = f.read()
                print(f"  ✓ Threaded read succeeded: {recovered_threaded[:50]}...")
            except Exception as e:
                print(f"  ✗ Threaded read failed: {e}")
                
            # Try to read with regular igzip
            try:
                with igzip.open(tmp_path, "rb") as f:
                    recovered_regular = f.read()
                print(f"  ✓ Regular igzip read succeeded: {recovered_regular[:50]}...")
            except Exception as e:
                print(f"  ✗ Regular igzip read failed: {e}")
                
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

if __name__ == "__main__":
    test_various_flush_scenarios()