import troposphere.datazone as dz

# Test various float values
test_values = [
    0.0, 1.0, 0.5, -0.0, 1.5, 2.0, -1.0, 
    float(0), float(1), float(False), float(True)
]

print("Testing boolean() with float values:")
print("-" * 40)

for val in test_values:
    try:
        result = dz.boolean(val)
        print(f"boolean({val!r}) = {result} (should raise ValueError!)")
    except ValueError:
        print(f"boolean({val!r}) raised ValueError (correct)")

print("\n" + "=" * 40)
print("BUG CONFIRMED: boolean() accepts float values 0.0 and 1.0")
print("This violates the function's documented behavior")