from cryptography.hazmat.primitives import keywrap
import traceback

print("Bug 1: Empty key wrap produces output < 16 bytes")
print("="*60)

# When wrapping an empty key with padding, the output is only 8 bytes
# But unwrap_with_padding requires at least 16 bytes
wrapping_key = b'\x00' * 16
empty_key = b""

wrapped = keywrap.aes_key_wrap_with_padding(wrapping_key, empty_key)
print(f"Wrapping empty key produces: {wrapped.hex()} ({len(wrapped)} bytes)")

# Check the logic in the wrap function
print("\nFrom the source code analysis:")
print("- Empty key has len=0")
print("- Padding: (8 - (0 % 8)) % 8 = 0")
print("- After padding: key_to_wrap = b'' + b'' = b'' (still empty)")
print("- Since len(key_to_wrap) == 0, neither branch is taken")
print("- So the AIV is returned directly: b'\\xa6\\x59\\x59\\xa6' + (0).to_bytes(4, 'big')")
print("- Result is 8 bytes")

print("\nBut unwrap_with_padding requires >= 16 bytes!")
try:
    unwrapped = keywrap.aes_key_unwrap_with_padding(wrapping_key, wrapped)
except keywrap.InvalidUnwrap as e:
    print(f"InvalidUnwrap: {e}")

print("\n" + "="*60)
print("Bug 2: Invalid input causes ValueError instead of InvalidUnwrap")
print("="*60)

# When unwrapping invalid data that's not a multiple of block size
# it crashes with ValueError instead of InvalidUnwrap
wrapping_key = b'\x00' * 16

# Test various invalid lengths
for length in [17, 18, 19, 20, 21, 22, 23, 25, 26]:
    wrapped_key = b'\x00' * length
    print(f"\nTrying to unwrap {length} bytes...")
    try:
        result = keywrap.aes_key_unwrap_with_padding(wrapping_key, wrapped_key)
        print(f"  Unexpectedly succeeded!")
    except keywrap.InvalidUnwrap as e:
        print(f"  InvalidUnwrap (expected): {e}")
    except ValueError as e:
        print(f"  ValueError (BUG!): {e}")
        
print("\n" + "="*60)
print("Analysis:")
print("When len(wrapped_key) > 16 but not multiple of 8,")
print("the code tries to split it into 8-byte chunks.")
print("This creates r list with wrong-sized last element,") 
print("causing _unwrap_core to fail with ValueError")
print("instead of proper InvalidUnwrap exception.")