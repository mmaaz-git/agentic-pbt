#!/usr/bin/env python3
import sys
import tempfile
import os

# Add the isal environment to the path
sys.path.insert(0, '/root/hypothesis-llm/envs/isal_env/lib/python3.13/site-packages')

import isal.igzip_threaded as igzip_threaded

def reproduce_bug():
    """Minimal reproduction of the flush bug."""
    chunks = [b'\x00', b'\x00\x00\x00\x00']
    threads = 1
    
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        print(f"Writing chunks to {tmp_path}")
        print(f"Chunks: {chunks}")
        print(f"Threads: {threads}")
        
        # Write chunks with flush after first chunk
        with igzip_threaded.open(tmp_path, "wb", threads=threads) as f:
            f.write(chunks[0])  # Write b'\x00'
            print("Wrote first chunk, calling flush...")
            f.flush()  # Flush after first write
            print("Flush complete, writing second chunk...")
            f.write(chunks[1])  # Write b'\x00\x00\x00\x00'
            print("Wrote second chunk")
        
        print("File written successfully, now attempting to read...")
        
        # Try to read it back - this should fail
        with igzip_threaded.open(tmp_path, "rb") as f:
            recovered = f.read()
            print(f"Successfully read back: {recovered}")
            
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        return False
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
    
    return True

if __name__ == "__main__":
    success = reproduce_bug()
    sys.exit(0 if success else 1)