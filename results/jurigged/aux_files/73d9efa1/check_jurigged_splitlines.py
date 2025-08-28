import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/jurigged_env/lib/python3.13/site-packages')

# Check how jurigged handles splitlines
from jurigged.recode import splitlines

# Test the behavior
test_strings = [
    "hello\nworld",
    "single line",
    "",
    "\n",
    "line1\nline2\nline3",
    "trailing newline\n",
]

print("Testing jurigged's splitlines behavior:")
for s in test_strings:
    lines = splitlines(s)
    print(f"Input: {repr(s)}")
    print(f"Split: {lines}")
    print(f"Length: {len(lines)}")
    print()

# Check the virtual_file function
from jurigged.recode import virtual_file
import linecache

# Test virtual_file
print("\n=== Testing virtual_file ===")
content = "def foo():\n    return 42\n"
filename = virtual_file("test", content)
print(f"Generated filename: {filename}")
print(f"Cached entry: {linecache.cache.get(filename)}")

# Test uniqueness
filename2 = virtual_file("test", content)
print(f"Second filename: {filename2}")
print(f"Are they different? {filename != filename2}")