"""Minimal reproduction of the scientific notation bug in webcolors."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/webcolors_env/lib/python3.13/site-packages')

import webcolors

# Test case 1: Scientific notation without decimal point
print("Testing scientific notation in percent values:")
try:
    result = webcolors.rgb_percent_to_rgb(('0%', '0%', '5e-324%'))
    print(f"Result: {result}")
except ValueError as e:
    print(f"ERROR: {e}")
    print("This is a bug - scientific notation is a valid way to represent numbers in CSS")

print("\n" + "="*50 + "\n")

# Test case 2: Scientific notation with decimal point (should work)
print("Testing scientific notation with decimal point:")
try:
    result = webcolors.rgb_percent_to_rgb(('0%', '0%', '1.5e2%'))
    print(f"Result: {result}")
except ValueError as e:
    print(f"ERROR: {e}")

print("\n" + "="*50 + "\n")

# Test case 3: Regular percent values (should work)
print("Testing regular percent values:")
try:
    result = webcolors.rgb_percent_to_rgb(('50%', '75%', '100%'))
    print(f"Result: {result}")
except ValueError as e:
    print(f"ERROR: {e}")

print("\n" + "="*50 + "\n")

# Root cause analysis
print("Root cause:")
print("The _normalize_percent_rgb function in webcolors/_normalization.py line 95:")
print('    percent = float(value) if "." in value else int(value)')
print("\nThis assumes that if there's no decimal point, the value is an integer.")
print("However, scientific notation like '5e-324' is a valid float representation")
print("that doesn't contain a decimal point, causing int() to fail.")
print("\nCSS supports scientific notation in numeric values, so this is a legitimate bug.")