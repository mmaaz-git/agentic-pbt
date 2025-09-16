"""Comprehensive verification of the Fernet non-ASCII token bug."""

from cryptography.fernet import Fernet, InvalidToken
import traceback

key = Fernet.generate_key()
f = Fernet(key)

# Test various invalid token types that should all raise InvalidToken
test_cases = [
    ("Non-ASCII string \\x80", "\x80"),
    ("Non-ASCII string with emoji", "🦄"),
    ("Unicode string with special chars", "tøken"),
    ("Mixed ASCII and non-ASCII", "abc\x80def"),
    ("Empty string", ""),
    ("Invalid base64 but valid ASCII", "not-valid-base64!"),
    ("Valid base64 but wrong format", "dGVzdA=="),  # "test" in base64
]

print("Testing Fernet.decrypt with various invalid tokens:\n")

for description, token in test_cases:
    print(f"Test: {description}")
    print(f"Token: {repr(token)}")
    
    try:
        result = f.decrypt(token)
        print(f"  ❌ UNEXPECTED: Decryption succeeded: {result}")
    except InvalidToken:
        print(f"  ✓ Got InvalidToken (expected)")
    except ValueError as e:
        print(f"  ❌ BUG: Got ValueError instead of InvalidToken: {e}")
    except TypeError as e:
        print(f"  ⚠ Got TypeError: {e}")
    except Exception as e:
        print(f"  ❌ Got unexpected exception {type(e).__name__}: {e}")
    print()

print("="*70)
print("ANALYSIS:")
print("The Fernet.decrypt method has inconsistent error handling.")
print("It should always raise InvalidToken for invalid input tokens,")
print("but it raises ValueError for non-ASCII strings instead.")
print("\nThis violates the API contract where InvalidToken should be raised")
print("for ALL invalid tokens, regardless of why they're invalid.")
print("="*70)