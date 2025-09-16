"""Minimal reproduction of the bug."""
from cryptography.fernet import Fernet, InvalidToken

# Test case 1: String with non-ASCII character
key = Fernet.generate_key()
f = Fernet(key)

# This should raise InvalidToken, but raises ValueError instead
try:
    f.decrypt('\x81')
    print("No exception raised - unexpected!")
except InvalidToken:
    print("InvalidToken raised - expected behavior")
except ValueError as e:
    print(f"ValueError raised instead of InvalidToken: {e}")
    print("This is a bug - decrypt should always raise InvalidToken for invalid tokens")

# Test case 2: More non-ASCII characters
test_cases = ['\x81', '\xff', 'Ā', '😀', '\u2022']

for token in test_cases:
    try:
        f.decrypt(token)
        print(f"Token {repr(token)}: No exception")
    except InvalidToken:
        print(f"Token {repr(token)}: InvalidToken (correct)")
    except ValueError as e:
        print(f"Token {repr(token)}: ValueError (bug!) - {e}")

# Test that bytes work correctly (as comparison)
print("\nBytes tokens (for comparison):")
for token in [b'\x81', b'\xff', b'invalid']:
    try:
        f.decrypt(token)
        print(f"Token {repr(token)}: No exception")
    except InvalidToken:
        print(f"Token {repr(token)}: InvalidToken (correct)")
    except ValueError as e:
        print(f"Token {repr(token)}: ValueError (bug!) - {e}")