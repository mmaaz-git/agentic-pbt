#!/usr/bin/env python3

import sys
import tempfile
import shutil
sys.path.insert(0, '/root/hypothesis-llm/envs/diskcache_env/lib/python3.13/site-packages')

from diskcache.core import Disk

# Minimal reproduction of the text storage bug
tmpdir = tempfile.mkdtemp()
try:
    disk = Disk(tmpdir, min_file_size=1000)
    
    # Create a string with carriage return that is large enough to be stored in a file
    original = "0" * 250 + "\r" + "0" * 1000
    print(f"Original length: {len(original)}")
    print(f"Original has \\r at position: {original.index(chr(13))}")
    
    # Store the value (should go to file due to size)
    size, mode, filename, db_value = disk.store(original, read=False)
    print(f"Stored: size={size}, mode={mode}, filename={filename}, db_value={db_value}")
    
    # Fetch it back
    retrieved = disk.fetch(mode, filename, db_value, read=False)
    print(f"Retrieved length: {len(retrieved)}")
    
    # Check if they match
    if original == retrieved:
        print("✓ Round-trip successful")
    else:
        print("✗ Round-trip FAILED!")
        print(f"First difference at position: {next(i for i, (a, b) in enumerate(zip(original, retrieved)) if a != b)}")
        print(f"Original char at difference: {repr(original[250])}")
        print(f"Retrieved char at difference: {repr(retrieved[250])}")
        
        # Check if the issue is with \r\n conversion
        if "\r\n" in retrieved and "\r\n" not in original:
            print("Issue: \\r was converted to \\r\\n")
        elif "\n" in retrieved and "\r" in original and "\n" not in original:
            print("Issue: \\r was converted to \\n")
            
finally:
    shutil.rmtree(tmpdir)