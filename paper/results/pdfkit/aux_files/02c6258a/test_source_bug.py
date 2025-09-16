import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pdfkit_env/lib/python3.13/site-packages')

from pdfkit.source import Source

# Test 1: Check the to_s() method with bytes input
print("Testing Source.to_s() with different inputs...")

# This should work - regular string
source1 = Source("test", "string")
result1 = source1.to_s()
print(f"String input: type={type(result1)}, value={result1}")

# Test with non-string source
source2 = Source(123, "string")
try:
    result2 = source2.to_s()
    print(f"Integer input: type={type(result2)}, value={result2}")
except Exception as e:
    print(f"Integer input failed: {e}")

# Test with list source
source3 = Source(["file1.html"], "file")
try:
    result3 = source3.to_s()
    print(f"List input: type={type(result3)}, value={result3}")
except Exception as e:
    print(f"List input failed: {e}")

# Test with bytes (simulating Python 2 style)
source4 = Source(b"test bytes", "string")
try:
    result4 = source4.to_s()
    print(f"Bytes input: type={type(result4)}, value={result4}")
except Exception as e:
    print(f"Bytes input failed: {e}")