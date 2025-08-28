from cryptography.hazmat.primitives import keywrap

# Bug 1: Empty key wrap/unwrap with padding fails
wrapping_key = b'\x00' * 16
empty_key = b""

print("Testing empty key wrap/unwrap with padding...")
try:
    wrapped = keywrap.aes_key_wrap_with_padding(wrapping_key, empty_key)
    print(f"Wrapped empty key successfully: {wrapped.hex()}")
    print(f"Wrapped length: {len(wrapped)}")
    
    # Try to unwrap
    unwrapped = keywrap.aes_key_unwrap_with_padding(wrapping_key, wrapped)
    print(f"Unwrapped successfully: {unwrapped!r}")
except Exception as e:
    print(f"ERROR: {e}")

print("\n" + "="*50 + "\n")

# Bug 2: Unwrap with padding crashes on certain inputs
print("Testing unwrap with padding on 17-byte input...")
wrapping_key = b'\x00' * 16
wrapped_key = b'\x00' * 17

try:
    result = keywrap.aes_key_unwrap_with_padding(wrapping_key, wrapped_key)
    print(f"Unexpectedly succeeded: {result!r}")
except keywrap.InvalidUnwrap as e:
    print(f"Expected InvalidUnwrap: {e}")
except ValueError as e:
    print(f"UNEXPECTED ValueError: {e}")
    print("This should have been InvalidUnwrap, not ValueError!")