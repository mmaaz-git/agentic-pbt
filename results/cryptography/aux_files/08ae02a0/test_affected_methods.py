"""Test which Fernet methods are affected by the non-ASCII bug."""

from cryptography.fernet import Fernet, InvalidToken

key = Fernet.generate_key()
f = Fernet(key)

# Non-ASCII test token
non_ascii = "\x80"

print("Testing which Fernet methods are affected by non-ASCII input:\n")

# Test decrypt
print("1. Fernet.decrypt()")
try:
    f.decrypt(non_ascii)
except ValueError:
    print("   ❌ Raises ValueError (should be InvalidToken)")
except InvalidToken:
    print("   ✓ Raises InvalidToken")

# Test decrypt with TTL
print("\n2. Fernet.decrypt() with ttl")
try:
    f.decrypt(non_ascii, ttl=100)
except ValueError:
    print("   ❌ Raises ValueError (should be InvalidToken)")
except InvalidToken:
    print("   ✓ Raises InvalidToken")

# Test decrypt_at_time
print("\n3. Fernet.decrypt_at_time()")
try:
    f.decrypt_at_time(non_ascii, ttl=100, current_time=1000000)
except ValueError:
    print("   ❌ Raises ValueError (should be InvalidToken)")
except InvalidToken:
    print("   ✓ Raises InvalidToken")

# Test extract_timestamp
print("\n4. Fernet.extract_timestamp()")
try:
    f.extract_timestamp(non_ascii)
except ValueError:
    print("   ❌ Raises ValueError (should be InvalidToken)")
except InvalidToken:
    print("   ✓ Raises InvalidToken")

# Test MultiFernet methods
from cryptography.fernet import MultiFernet

mf = MultiFernet([f])

print("\n5. MultiFernet.decrypt()")
try:
    mf.decrypt(non_ascii)
except ValueError:
    print("   ❌ Raises ValueError (should be InvalidToken)")
except InvalidToken:
    print("   ✓ Raises InvalidToken")

print("\n6. MultiFernet.rotate()")
try:
    mf.rotate(non_ascii)
except ValueError:
    print("   ❌ Raises ValueError (should be InvalidToken)")  
except InvalidToken:
    print("   ✓ Raises InvalidToken")

print("\n7. MultiFernet.extract_timestamp()")
try:
    mf.extract_timestamp(non_ascii)
except ValueError:
    print("   ❌ Raises ValueError (should be InvalidToken)")
except InvalidToken:
    print("   ✓ Raises InvalidToken")