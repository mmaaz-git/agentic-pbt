import tempfile
import os
import Cython.Build.Cache

# Test 1: Create new files each time to avoid caching issues
print("Test 1: Using different file paths")
with tempfile.NamedTemporaryFile(delete=False) as tmp1:
    tmp1.write(b'\x00')
    tmp1.flush()
    path1 = tmp1.name
    hash1 = Cython.Build.Cache.file_hash(path1)
    print(f"Hash of {path1} with b'\\x00': {hash1}")
    os.unlink(path1)

with tempfile.NamedTemporaryFile(delete=False) as tmp2:
    tmp2.write(b'\x00x')
    tmp2.flush()
    path2 = tmp2.name
    hash2 = Cython.Build.Cache.file_hash(path2)
    print(f"Hash of {path2} with b'\\x00x': {hash2}")
    os.unlink(path2)

print(f"Hashes are {'the same' if hash1 == hash2 else 'different'}")

# Test 2: Check if it's a caching issue
print("\nTest 2: Checking caching behavior")
with tempfile.NamedTemporaryFile(delete=False) as tmp:
    tmp.write(b'\x00')
    tmp.flush()
    path = tmp.name
    
    # First call
    hash1 = Cython.Build.Cache.file_hash(path)
    print(f"First call - Hash of file with b'\\x00': {hash1}")
    
    # Modify file
    with open(path, 'wb') as f:
        f.write(b'\x00x')
    
    # Second call - might be cached!
    hash2 = Cython.Build.Cache.file_hash(path)
    print(f"Second call - Hash of file with b'\\x00x': {hash2}")
    
    # Clear cache and try again
    Cython.Build.Cache.file_hash.cache_clear()
    hash3 = Cython.Build.Cache.file_hash(path)
    print(f"After cache clear - Hash of file with b'\\x00x': {hash3}")
    
    os.unlink(path)

# Test 3: Check what the paths include in the hash
print("\nTest 3: Understanding path influence on hash")
with tempfile.NamedTemporaryFile(delete=False, prefix="test1_") as tmp1:
    tmp1.write(b'\x00')
    tmp1.flush()
    path1 = tmp1.name
    hash1 = Cython.Build.Cache.file_hash(path1)
    print(f"Path: {path1}")
    print(f"Hash: {hash1}")
    os.unlink(path1)

with tempfile.NamedTemporaryFile(delete=False, prefix="test2_") as tmp2:
    tmp2.write(b'\x00')
    tmp2.flush()
    path2 = tmp2.name
    hash2 = Cython.Build.Cache.file_hash(path2)
    print(f"Path: {path2}")
    print(f"Hash: {hash2}")
    os.unlink(path2)

print(f"Same content, different paths - hashes are {'the same' if hash1 == hash2 else 'different'}")