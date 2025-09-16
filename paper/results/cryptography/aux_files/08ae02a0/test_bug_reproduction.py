"""Reproducing the bug with Fernet.decrypt handling non-ASCII strings."""

from cryptography.fernet import Fernet, InvalidToken

# Create a Fernet instance
key = Fernet.generate_key()
f = Fernet(key)

# Test with non-ASCII string
non_ascii_token = "\x80"  # Non-ASCII character

print("Testing Fernet.decrypt with non-ASCII string token...")
print(f"Token: repr({repr(non_ascii_token)})")

try:
    result = f.decrypt(non_ascii_token)
    print(f"Unexpectedly succeeded: {result}")
except InvalidToken as e:
    print(f"Got InvalidToken (expected): {e}")
except ValueError as e:
    print(f"Got ValueError (unexpected - should be InvalidToken): {e}")
except Exception as e:
    print(f"Got unexpected exception type {type(e).__name__}: {e}")

print("\n" + "="*60)
print("According to Fernet documentation and API contract:")
print("- decrypt() should raise InvalidToken for invalid tokens")
print("- ValueError indicates a programming error, not invalid data")
print("- Non-ASCII strings are invalid tokens and should raise InvalidToken")
print("="*60)