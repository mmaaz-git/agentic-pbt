import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pdfkit_env/lib/python3.13/site-packages')

from pdfkit.source import Source

print("Testing Source.to_s() with non-string inputs that could be valid HTML...")

# Test cases that could be valid HTML content but aren't strings
test_cases = [
    (123, "Integer that could be HTML content"),
    (45.67, "Float that could be HTML content"),
    (None, "None value"),
    (True, "Boolean value"),
    ([], "Empty list"),
    ({}, "Empty dict"),
]

for value, description in test_cases:
    print(f"\nTest: {description}")
    print(f"  Input: {value} (type: {type(value).__name__})")
    source = Source(value, "string")
    try:
        result = source.to_s()
        print(f"  Success: returned '{result}' (type: {type(result).__name__})")
    except Exception as e:
        print(f"  Failed: {e}")

# Also test the unicode function directly
print("\n\nTesting unicode function behavior in source.py:")
print("Line 57 calls: unicode(self.source, 'utf-8')")
print("This assumes self.source is a bytes-like object, but it could be any type")

# The actual bug is in source.py line 57:
# It calls unicode(self.source, 'utf-8') which expects bytes,
# but self.source could be any type when Source is created with type='string'