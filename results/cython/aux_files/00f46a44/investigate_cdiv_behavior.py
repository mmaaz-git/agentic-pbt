import Cython.Shadow as Shadow
import math

print("Comparing cdiv with different division behaviors:\n")
print("a\tb\ta/b\tfloor\ttrunc\tcdiv\tPy //")
print("-" * 60)

test_cases = [
    (7, 3),
    (-7, 3),
    (7, -3),
    (-7, -3),
    (3, -2),
    (-3, 2),
    (10, 3),
    (-10, 3),
    (10, -3),
    (-10, -3)
]

for a, b in test_cases:
    exact = a / b
    floor_div = math.floor(exact)
    trunc_div = math.trunc(exact)  # C-style truncation toward zero
    cdiv_result = Shadow.cdiv(a, b)
    py_floordiv = a // b
    
    print(f"{a}\t{b}\t{exact:.2f}\t{floor_div}\t{trunc_div}\t{cdiv_result}\t{py_floordiv}")

print("\nConclusion:")
print("cdiv appears to implement floor division (Python //) not C-style truncation")

# Let's verify the mathematical property still holds
print("\nVerifying a = cdiv(a,b) * b + cmod(a,b):")
for a, b in test_cases:
    q = Shadow.cdiv(a, b)
    r = Shadow.cmod(a, b)
    reconstructed = q * b + r
    print(f"  {a} = {q} * {b} + {r} = {reconstructed} ✓" if reconstructed == a else f"  {a} ≠ {q} * {b} + {r} = {reconstructed} ✗")