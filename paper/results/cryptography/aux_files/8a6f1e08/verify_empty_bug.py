from cryptography.hazmat.primitives import keywrap

# Verify the empty key bug more thoroughly
print("Testing various small key sizes with wrap_with_padding:")
print("="*60)

wrapping_key = b'\x00' * 16

for key_size in range(0, 9):
    key_to_wrap = b'A' * key_size
    wrapped = keywrap.aes_key_wrap_with_padding(wrapping_key, key_to_wrap)
    
    print(f"\nKey size: {key_size} bytes")
    print(f"  Wrapped: {wrapped.hex()} ({len(wrapped)} bytes)")
    
    # Check if padding calculation causes the issue
    pad = (8 - (key_size % 8)) % 8
    padded_size = key_size + pad
    print(f"  Padding: {pad} bytes, padded size: {padded_size}")
    
    # Try to unwrap
    try:
        unwrapped = keywrap.aes_key_unwrap_with_padding(wrapping_key, wrapped)
        print(f"  Unwrapped successfully: {unwrapped!r}")
        assert unwrapped == key_to_wrap, f"Round-trip failed!"
    except keywrap.InvalidUnwrap as e:
        print(f"  ERROR: {e}")
        
print("\n" + "="*60)
print("Analysis:")
print("When key_size is 0, padding is (8 - 0) % 8 = 0")
print("So padded key remains empty (0 bytes)")
print("The code then returns just the AIV (8 bytes)")
print("But unwrap requires at least 16 bytes!")
print("\nThis is a genuine bug in the wrap_with_padding implementation")