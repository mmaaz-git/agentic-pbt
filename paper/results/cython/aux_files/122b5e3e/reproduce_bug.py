import Cython.Shadow as cs

# The failing test case
a = 9007199254740993
b = 1

# What cdiv returns
result = cs.cdiv(a, b)

# What we expected (C-style division, truncation toward zero)
expected = int(a / b)

print(f"Testing cdiv({a}, {b})")
print(f"Result from cdiv: {result}")
print(f"Expected (int(a/b)): {expected}")
print(f"Direct division a/b: {a/b}")
print(f"Direct integer division a//b: {a//b}")
print(f"Bug: result != expected: {result != expected}")

# This is around 2^53, the limit of double precision
print(f"\nNote: {a} is close to 2^53 = {2**53}")
print(f"This is the limit of exact integer representation in double precision")

# Let's verify the floating point precision issue
print(f"\nFloating point test:")
print(f"float(a) == a: {float(a) == a}")
print(f"int(float(a)): {int(float(a))}")
print(f"Difference: {a - int(float(a))}")