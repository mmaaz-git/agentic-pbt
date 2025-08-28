"""Minimal reproductions of the bugs found."""

import tabulate

print("Bug 1: String 'True' causes ValueError")
print("=" * 50)
try:
    # This should work - mixed types in columns are normal
    data = [[0.0], ['True']]
    result = tabulate.tabulate(data)
    print("Unexpectedly succeeded!")
    print(result)
except ValueError as e:
    print(f"ValueError: {e}")
    print(f"Input data: {data}")
    print()
    print("This is a bug because:")
    print("- Mixed types in columns should be handled gracefully")
    print("- The string 'True' should be treated as a string, not parsed as boolean/float")
    print("- Other strings like 'Hello' work fine, only 'True'/'False' cause issues")

print("\n" + "=" * 50)
print("Bug 2: Pipe character in data breaks pipe format alignment")
print("=" * 50)

# This causes misaligned columns in pipe format
data = [[None], ['0|']]
result = tabulate.tabulate(data, tablefmt='pipe')
print("Result with pipe format:")
print(result)
print()
print("Lines in result:")
for i, line in enumerate(result.split('\n')):
    print(f"Line {i}: {repr(line)}")
    pipe_positions = [j for j, c in enumerate(line) if c == '|']
    print(f"  Pipe positions: {pipe_positions}")

print()
print("This is a bug because:")
print("- The pipe character in data should be escaped or handled properly")
print("- It causes misaligned columns when using pipe table format")
print("- Column separators should be at consistent positions across all rows")

# Let's also test if other formats have similar issues
print("\n" + "=" * 50)
print("Testing other formats with special characters:")
test_data = [['normal'], ['with|pipe'], ['with+plus'], ['with-minus']]
for fmt in ['pipe', 'grid', 'orgtbl']:
    print(f"\nFormat: {fmt}")
    try:
        result = tabulate.tabulate(test_data, tablefmt=fmt)
        lines = result.split('\n')
        # Check for alignment issues
        data_lines = [l for l in lines if any(c.isalnum() for c in l)]
        if fmt in ['pipe', 'grid', 'orgtbl'] and '|' in result:
            positions = []
            for line in data_lines:
                pipe_pos = [i for i, c in enumerate(line) if c == '|']
                positions.append(pipe_pos)
            
            if positions and not all(p == positions[0] for p in positions[1:]):
                print(f"  ⚠️ MISALIGNED! Column positions vary:")
                for i, (line, pos) in enumerate(zip(data_lines, positions)):
                    print(f"    Line {i}: {repr(line[:40])}... positions: {pos}")
            else:
                print(f"  ✓ Aligned correctly")
    except Exception as e:
        print(f"  ✗ Error: {e}")