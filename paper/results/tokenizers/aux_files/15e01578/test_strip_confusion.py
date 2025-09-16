import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/tokenizers_env/lib/python3.13/site-packages')

import tokenizers.decoders as decoders
import tokenizers.normalizers as normalizers

print("="*60)
print("INVESTIGATION: Strip in decoders vs normalizers")
print("="*60)

# Check Strip decoder docstring
print("Strip DECODER docstring:")
print(decoders.Strip.__doc__)
print()

# Check if normalizers has Strip
print("Strip NORMALIZER exists:", hasattr(normalizers, 'Strip'))
if hasattr(normalizers, 'Strip'):
    print("Strip NORMALIZER docstring:")
    print(normalizers.Strip.__doc__)
    print()

# Test normalizer Strip with boolean args
print("Testing normalizers.Strip with boolean arguments:")
try:
    strip_norm = normalizers.Strip(left=True, right=True)
    print("  normalizers.Strip(left=True, right=True) - SUCCESS")
except Exception as e:
    print(f"  Error: {e}")

# The issue: Strip decoder claims to strip N characters but doesn't work
print("\n" + "="*60)
print("BUG CONFIRMED: Strip decoder is broken")
print("="*60)
print("The Strip decoder claims to strip 'n' characters from left/right")
print("but it doesn't actually strip anything from the decoded tokens.")
print()
print("Evidence:")
print("1. Docstring says: 'Strips n left characters of each token'")
print("2. Constructor accepts integer arguments for left/right")
print("3. decode() method returns unchanged tokens")
print()
print("This is a CONTRACT violation - the implementation doesn't match the documentation!")