import Cython.Shadow as cs

# Test various cases to understand cdiv behavior
test_cases = [
    (9007199254740993, 1),
    (10, 3),
    (-10, 3),
    (10, -3),
    (-10, -3),
]

print("Comparing cdiv with various division methods:\n")
print("a, b | cdiv(a,b) | a//b (Python) | int(a/b) | C-style expected")
print("-" * 70)

for a, b in test_cases:
    cdiv_result = cs.cdiv(a, b)
    py_floordiv = a // b
    int_truediv = int(a / b)
    
    # C-style division truncates toward zero
    # For positive results, it's the same as floor division
    # For negative results, it rounds toward zero (unlike Python's floor)
    if (a < 0) != (b < 0):  # Different signs, result should be negative
        c_expected = -(-a // b) if a < 0 else -(a // -b)
    else:
        c_expected = abs(a) // abs(b)
    
    print(f"{a:15}, {b:3} | {cdiv_result:9} | {py_floordiv:13} | {int_truediv:8} | {c_expected:8}")

# Check the specific failing case
print("\n" + "="*70)
print("Analyzing the specific failure:")
a = 9007199254740993
b = 1

print(f"\nFor a={a}, b={b}:")
print(f"cdiv(a, b) = {cs.cdiv(a, b)}")
print(f"Python a // b = {a // b}")
print(f"int(a / b) = {int(a / b)} (loses precision due to float conversion)")
print(f"\nThe issue: int(a/b) loses precision for integers > 2^53")
print(f"cdiv correctly returns {cs.cdiv(a, b)}, which equals a//b = {a//b}")
print(f"My test incorrectly expected int(a/b) = {int(a/b)}")