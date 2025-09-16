import tempfile
import os
import Cython.Build.Cache

# Create a test file with a single null byte
with tempfile.NamedTemporaryFile(delete=False) as tmp:
    tmp.write(b'\x00')
    tmp.flush()
    path = tmp.name
    
    # Get hash of file with single null byte
    hash1 = Cython.Build.Cache.file_hash(path)
    print(f"Hash of file with b'\\x00': {hash1}")
    
    # Modify file to contain null byte + 'x'
    with open(path, 'wb') as f:
        f.write(b'\x00x')
    
    # Get hash of modified file
    hash2 = Cython.Build.Cache.file_hash(path)
    print(f"Hash of file with b'\\x00x': {hash2}")
    
    print(f"Hashes are {'the same' if hash1 == hash2 else 'different'}")
    
    # Clean up
    os.unlink(path)

# Let's also test what the actual file_hash function does
print("\n--- Debugging the file_hash function ---")
import hashlib

def debug_file_hash(content, filename="test"):
    """Debug version of the file_hash function"""
    path = os.path.normpath(filename)
    prefix = ("%d:%s" % (len(path), path)).encode("UTF-8")
    print(f"  Prefix: {prefix}")
    m = hashlib.sha256(prefix)
    m.update(content)
    return m.hexdigest()

# Test with our cases
hash_debug1 = debug_file_hash(b'\x00', "test")
hash_debug2 = debug_file_hash(b'\x00x', "test")
print(f"Debug hash of b'\\x00': {hash_debug1}")
print(f"Debug hash of b'\\x00x': {hash_debug2}")
print(f"Debug hashes are {'the same' if hash_debug1 == hash_debug2 else 'different'}")

# Actually look at the source of file_hash to understand what's happening
print("\n--- Checking actual implementation ---")
import inspect
print(inspect.getsource(Cython.Build.Cache.file_hash.__wrapped__))