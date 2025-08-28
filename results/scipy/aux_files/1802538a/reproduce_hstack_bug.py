import scipy.sparse as sp
import numpy as np

print("BUG: scipy.sparse.hstack crashes with empty list")
print("=" * 60)

print("\nTesting sp.hstack([])...")
try:
    result = sp.hstack([])
    print(f"Unexpected success! Result: {result}")
except IndexError as e:
    print(f"IndexError: {e}")
    print("\nThis is a BUG - hstack should handle empty list gracefully")
    print("Either return an empty matrix or raise a ValueError with clear message")
except ValueError as e:
    print(f"ValueError (expected): {e}")

print("\n" + "=" * 60)
print("Testing sp.vstack([]) for comparison...")
try:
    result = sp.vstack([])
    print(f"Result: {result}")
except IndexError as e:
    print(f"IndexError: {e}")
    print("vstack also crashes!")
except ValueError as e:
    print(f"ValueError: {e}")

print("\n" + "=" * 60)
print("Testing numpy for comparison...")
try:
    result = np.hstack([])
    print(f"np.hstack([]) returns: {result}")
except (ValueError, IndexError) as e:
    print(f"numpy raises: {type(e).__name__}: {e}")

try:
    result = np.vstack([])
    print(f"np.vstack([]) returns: {result}")
except (ValueError, IndexError) as e:
    print(f"numpy raises: {type(e).__name__}: {e}")

print("\n" + "=" * 60)
print("ANALYSIS:")
print("scipy.sparse.hstack([]) crashes with IndexError")
print("while numpy.vstack([]) properly raises ValueError")
print("This is a crash bug that should be fixed.")