"""Investigate the True/False string parsing bug in more detail."""

import tabulate

print("Testing various string values that might be parsed incorrectly:")
print("=" * 60)

test_cases = [
    [[0.0], ['True']],
    [[0.0], ['False']],
    [[0.0], ['true']],  
    [[0.0], ['false']],
    [[0.0], ['TRUE']],
    [[0.0], ['Yes']],
    [[0.0], ['No']],
    [[0.0], ['1']],
    [[0.0], ['0']],
    [[0.0], ['None']],
    [[0.0], ['null']],
    [[0.0], ['Hello']],  # Control - should work
]

for data in test_cases:
    string_val = data[1][0]
    try:
        result = tabulate.tabulate(data)
        print(f"✓ '{string_val}': Success")
    except ValueError as e:
        print(f"✗ '{string_val}': ValueError - {e}")
    except Exception as e:
        print(f"✗ '{string_val}': {type(e).__name__} - {e}")

print("\n" + "=" * 60)
print("Testing with disable_numparse=True (should work):")
print("=" * 60)

problem_data = [[0.0], ['True']]
try:
    result = tabulate.tabulate(problem_data, disable_numparse=True)
    print("✓ Success with disable_numparse=True")
    print("Result:")
    print(result)
except Exception as e:
    print(f"✗ Still fails: {e}")

print("\n" + "=" * 60)
print("Root cause analysis:")
print("=" * 60)
print("The bug occurs because tabulate tries to be 'smart' about detecting")
print("numeric data and attempts to parse 'True' as a float, which fails.")
print("This violates the principle that mixed-type columns should be handled gracefully.")

# Let's see what the actual parsing logic does
print("\nLet's trace what tabulate does with 'True':")
# We can check if it tries to detect it as numeric
import sys
from io import StringIO

# Capture any debug output
old_stdout = sys.stdout
sys.stdout = StringIO()

try:
    # This will error but let's see
    tabulate.tabulate([[0.0], ['True']])
except:
    pass

output = sys.stdout.getvalue()
sys.stdout = old_stdout

if output:
    print("Debug output:", output)
    
# Check if True without quotes works
print("\nTesting with actual boolean True (not string):")
try:
    result = tabulate.tabulate([[0.0], [True]])
    print("✓ Boolean True works")
    print("Result:")
    print(result)
except Exception as e:
    print(f"✗ Boolean True fails: {e}")