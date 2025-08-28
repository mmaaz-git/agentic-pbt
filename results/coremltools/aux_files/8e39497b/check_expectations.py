import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/coremltools_env/lib/python3.13/site-packages')

from coremltools.converters.mil.input_types import EnumeratedShapes

print("Checking EnumeratedShapes documentation and expected behavior...")
print("\n" + "="*60)
print("EnumeratedShapes docstring:")
print("="*60)
print(EnumeratedShapes.__doc__)
print("="*60)

print("\nKey observations:")
print("1. Doc says 'The valid shapes of the inputs' (plural)")
print("2. Example shows shapes with SAME length: (2,4,64,64), (2,4,48,48), (2,4,32,32)")
print("3. No explicit requirement that shapes must have same length")
print("4. Parameter is called 'shapes' implying multiple different shapes are valid")

print("\nChecking if same-length shapes work:")
try:
    same_length = EnumeratedShapes([(1, 2), (3, 4), (5, 6)])
    print(f"SUCCESS: Same-length shapes work: {same_length}")
except Exception as e:
    print(f"FAIL: Even same-length shapes fail: {e}")

print("\nChecking the use case in ML:")
print("- Supporting different input formats is common in ML models")
print("- E.g., a model that accepts both flattened (784,) and image (28,28) inputs")
print("- Or RGB (H,W,3) and grayscale (H,W) images")
print("- This bug prevents these legitimate use cases")