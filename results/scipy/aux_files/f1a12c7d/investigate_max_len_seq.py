import scipy.signal as sig
import numpy as np

print("Testing max_len_seq with different nbits values:")

# Test nbits = 1
print("\nnbits = 1:")
try:
    seq, state = sig.max_len_seq(1)
    print(f"  Success: seq length = {len(seq)}, expected = {2**1 - 1}")
except ValueError as e:
    print(f"  Error: {e}")

# Test nbits = 2
print("\nnbits = 2:")
try:
    seq, state = sig.max_len_seq(2)
    print(f"  Success: seq length = {len(seq)}, expected = {2**2 - 1}")
    print(f"  Sequence: {seq}")
except ValueError as e:
    print(f"  Error: {e}")

# Check documentation
print("\nChecking what nbits values are supported...")
print("From error message, it seems nbits must be one of the predefined values")

# Let's see what the minimum supported value is
for n in range(1, 33):
    try:
        seq, _ = sig.max_len_seq(n)
        print(f"nbits={n}: supported (length={len(seq)})")
    except ValueError:
        print(f"nbits={n}: NOT supported")