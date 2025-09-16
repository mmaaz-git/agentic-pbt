import Cython.Shadow as Shadow

# Investigate typeof failure
print("typeof returns strings, not type objects:")
print(f"  typeof(42) = {repr(Shadow.typeof(42))} (type: {type(Shadow.typeof(42))})")
print(f"  Expected: {repr(int)} (type: {type(int)})")

# Investigate cdiv failure
print("\ncdiv truncation issue:")
print(f"  3 / -2 = {3 / -2}")
print(f"  cdiv(3, -2) = {Shadow.cdiv(3, -2)}")
print(f"  Expected (truncate toward zero): -1")
print(f"  Python floor division: 3 // -2 = {3 // -2}")

print("\nMore cdiv examples:")
for a, b in [(7, 3), (-7, 3), (7, -3), (-7, -3), (3, -2), (-3, 2)]:
    print(f"  cdiv({a}, {b}) = {Shadow.cdiv(a, b)}, expected truncation of {a/b} = {int(a/b) if a/b >= 0 else (int(a/b) if a/b == int(a/b) else int(a/b)+1)}")