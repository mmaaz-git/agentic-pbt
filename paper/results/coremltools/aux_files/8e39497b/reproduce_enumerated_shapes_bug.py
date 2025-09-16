import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/coremltools_env/lib/python3.13/site-packages')

from coremltools.converters.mil.input_types import EnumeratedShapes

print("Testing EnumeratedShapes with different length shapes...")

# This should work according to the documentation
# EnumeratedShapes allows multiple valid shapes for inputs
try:
    # Different length shapes - this is a common use case!
    # For example, supporting both 1D and 2D inputs
    shapes = [[1], [1, 1]]  # Minimal failing case from Hypothesis
    enum_shapes = EnumeratedShapes(shapes)
    print(f"SUCCESS: Created EnumeratedShapes with shapes: {shapes}")
except IndexError as e:
    print(f"BUG FOUND: IndexError when creating EnumeratedShapes with different length shapes")
    print(f"Shapes: {shapes}")
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\nTrying another example with more realistic shapes...")
try:
    # Common use case: supporting different image sizes
    shapes = [(224, 224), (224, 224, 3)]  # 2D grayscale vs 3D RGB
    enum_shapes = EnumeratedShapes(shapes)
    print(f"SUCCESS: Created EnumeratedShapes with shapes: {shapes}")
except IndexError as e:
    print(f"BUG FOUND: IndexError with shapes: {shapes}")
    print(f"Error: {e}")