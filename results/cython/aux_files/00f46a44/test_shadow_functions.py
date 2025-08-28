import Cython.Shadow as Shadow

# Test cdiv and cmod functions
print("Testing cdiv (C-style division):")
print(f"  cdiv(7, 3) = {Shadow.cdiv(7, 3)}")
print(f"  cdiv(-7, 3) = {Shadow.cdiv(-7, 3)}")
print(f"  cdiv(7, -3) = {Shadow.cdiv(7, -3)}")
print(f"  cdiv(-7, -3) = {Shadow.cdiv(-7, -3)}")

print("\nTesting cmod (C-style modulo):")
print(f"  cmod(7, 3) = {Shadow.cmod(7, 3)}")
print(f"  cmod(-7, 3) = {Shadow.cmod(-7, 3)}")
print(f"  cmod(7, -3) = {Shadow.cmod(7, -3)}")
print(f"  cmod(-7, -3) = {Shadow.cmod(-7, -3)}")

print("\nCompare with Python division and modulo:")
print(f"  Python: 7 // 3 = {7 // 3}, 7 % 3 = {7 % 3}")
print(f"  Python: -7 // 3 = {-7 // 3}, -7 % 3 = {-7 % 3}")
print(f"  Python: 7 // -3 = {7 // -3}, 7 % -3 = {7 % -3}")
print(f"  Python: -7 // -3 = {-7 // -3}, -7 % -3 = {-7 % -3}")

# Test sizeof
print("\nTesting sizeof:")
print(f"  sizeof(42) = {Shadow.sizeof(42)}")
print(f"  sizeof('hello') = {Shadow.sizeof('hello')}")
print(f"  sizeof([1,2,3]) = {Shadow.sizeof([1,2,3])}")

# Test typeof
print("\nTesting typeof:")
print(f"  typeof(42) = {Shadow.typeof(42)}")
print(f"  typeof('hello') = {Shadow.typeof('hello')}")
print(f"  typeof([1,2,3]) = {Shadow.typeof([1,2,3])}")