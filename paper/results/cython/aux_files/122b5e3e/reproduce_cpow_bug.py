import Cython.Shadow as cs

# cpow should be a power function taking base and exponent
# But it only accepts one argument

print("Testing cpow function:")
print("Expected: cpow(base, exponent) computes base^exponent")
print()

# This should work but doesn't
try:
    result = cs.cpow(2, 3)
    print(f"cpow(2, 3) = {result}")
except TypeError as e:
    print(f"cpow(2, 3) failed with: {e}")

# Checking what it actually does
result = cs.cpow(2)
print(f"cpow(2) returns: {result}")
print(f"Type: {type(result)}")

# The issue: cpow is implemented as: lambda _: _EmptyDecoratorAndManager()
# It's a stub that doesn't implement the actual power function