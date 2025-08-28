"""Test the bug across all methods that accept tokens."""
from cryptography.fernet import Fernet, MultiFernet, InvalidToken

key = Fernet.generate_key()
f = Fernet(key)
mf = MultiFernet([f])

# Test invalid token with non-ASCII character
invalid_token = '\x81'

print("Testing all Fernet methods that accept tokens:")
print("=" * 50)

# Test decrypt
print("1. Fernet.decrypt():")
try:
    f.decrypt(invalid_token)
except InvalidToken:
    print("   ✓ InvalidToken raised (correct)")
except ValueError as e:
    print(f"   ✗ ValueError raised (bug): {e}")

# Test decrypt_at_time
print("\n2. Fernet.decrypt_at_time():")
try:
    f.decrypt_at_time(invalid_token, ttl=100, current_time=1000)
except InvalidToken:
    print("   ✓ InvalidToken raised (correct)")
except ValueError as e:
    print(f"   ✗ ValueError raised (bug): {e}")

# Test extract_timestamp
print("\n3. Fernet.extract_timestamp():")
try:
    f.extract_timestamp(invalid_token)
except InvalidToken:
    print("   ✓ InvalidToken raised (correct)")
except ValueError as e:
    print(f"   ✗ ValueError raised (bug): {e}")

print("\nTesting MultiFernet methods:")
print("=" * 50)

# Test MultiFernet.decrypt
print("4. MultiFernet.decrypt():")
try:
    mf.decrypt(invalid_token)
except InvalidToken:
    print("   ✓ InvalidToken raised (correct)")
except ValueError as e:
    print(f"   ✗ ValueError raised (bug): {e}")

# Test MultiFernet.decrypt_at_time
print("\n5. MultiFernet.decrypt_at_time():")
try:
    mf.decrypt_at_time(invalid_token, ttl=100, current_time=1000)
except InvalidToken:
    print("   ✓ InvalidToken raised (correct)")
except ValueError as e:
    print(f"   ✗ ValueError raised (bug): {e}")

# Test MultiFernet.rotate
print("\n6. MultiFernet.rotate():")
try:
    mf.rotate(invalid_token)
except InvalidToken:
    print("   ✓ InvalidToken raised (correct)")
except ValueError as e:
    print(f"   ✗ ValueError raised (bug): {e}")

# Test MultiFernet.extract_timestamp
print("\n7. MultiFernet.extract_timestamp():")
try:
    mf.extract_timestamp(invalid_token)
except InvalidToken:
    print("   ✓ InvalidToken raised (correct)")
except ValueError as e:
    print(f"   ✗ ValueError raised (bug): {e}")