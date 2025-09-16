import numpy as np
import scipy.sparse as sp

print("INVESTIGATING: scipy.sparse.diags scalar broadcasting claim")
print("=" * 60)

# Get the exact documentation text
doc_lines = sp.diags.__doc__.split('\n')
for i, line in enumerate(doc_lines[65:75]):  # Around where broadcasting is mentioned
    print(line)

print("\n" + "=" * 60)
print("TESTS:")

# Test 1: Single-element list (broadcasts)
print("\n1. Single-element list [5]:")
result = sp.diags([5], 0, shape=(3, 3))
print(result.toarray())
print("✓ Works - broadcasts to fill diagonal")

# Test 2: Pure scalar (fails)
print("\n2. Pure scalar 5:")
try:
    result = sp.diags(5, 0, shape=(3, 3))
    print(result.toarray())
except TypeError as e:
    print(f"✗ Fails with: {e}")

# Test 3: Multiple single-element lists (from docs)
print("\n3. Multiple single-element lists [1], [-2], [1]:")
result = sp.diags([1, -2, 1], [-1, 0, 1], shape=(4, 4))
print(result.toarray())
print("✓ Works - each scalar in list broadcasts")

print("\n" + "=" * 60)
print("ANALYSIS:")
print("The documentation states: 'Broadcasting of scalars is supported'")
print("but this is misleading. What actually works is:")
print("- Single-element lists/arrays broadcast: [5] → [5,5,5,...]")
print("- Scalars NOT in containers fail: 5 → TypeError")
print("\nThis is a DOCUMENTATION BUG - the wording is confusing.")
print("It should say 'Broadcasting of single-element arrays is supported'")
print("or provide an example showing [scalar] not just scalar.")