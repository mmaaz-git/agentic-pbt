import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/coremltools_env/lib/python3.13/site-packages')

print("Proposed fix for EnumeratedShapes bug:")
print("\nThe fix needs to handle shapes of different lengths properly.")
print("The symbolic_shape should have length equal to the maximum shape length.")
print("\nHere's the fix (lines 556-564 in input_types.py):")

fix = '''
# OLD CODE (buggy):
self.symbolic_shape = self.shapes[0].symbolic_shape
for shape in self.shapes:
    for idx, s in enumerate(shape.symbolic_shape):
        if is_symbolic(self.symbolic_shape[idx]):  # BUG: IndexError here
            continue
        elif is_symbolic(s):
            self.symbolic_shape[idx] = s
        elif s != self.symbolic_shape[idx]:
            self.symbolic_shape[idx] = get_new_symbol()

# FIXED CODE:
# Find the maximum number of dimensions across all shapes
max_rank = max(len(shape.symbolic_shape) for shape in self.shapes)

# Initialize symbolic_shape with new symbols for all dimensions
self.symbolic_shape = [get_new_symbol() for _ in range(max_rank)]

# Now process each shape
for shape in self.shapes:
    for idx, s in enumerate(shape.symbolic_shape):
        # Since we've pre-allocated symbolic_shape with max_rank length,
        # idx will never be out of bounds
        if is_symbolic(self.symbolic_shape[idx]):
            continue
        elif is_symbolic(s):
            self.symbolic_shape[idx] = s
        elif s != self.symbolic_shape[idx]:
            self.symbolic_shape[idx] = get_new_symbol()
'''

print(fix)