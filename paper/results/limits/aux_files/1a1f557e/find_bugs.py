import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/limits_env/lib/python3.13/site-packages')

# Direct test execution to find bugs
def test_safe_string_bug():
    from limits.limits import safe_string
    
    # Test with invalid UTF-8 bytes
    invalid_bytes = b'\xff\xfe'
    try:
        result = safe_string(invalid_bytes)
        return f"No error, result: {repr(result)}"
    except UnicodeDecodeError as e:
        return f"BUG FOUND: UnicodeDecodeError - {str(e)}"
    except Exception as e:
        return f"Other error: {e}"

def test_parse_zero():
    from limits import parse
    try:
        result = parse("0/second")
        return f"Accepts 0: amount={result.amount}"
    except Exception as e:
        return f"Rejected: {e}"

# Execute tests
print("Test 1 - safe_string with invalid UTF-8:")
print(test_safe_string_bug())

print("\nTest 2 - parse with zero:")
print(test_parse_zero())

# Direct execution of the problematic code
print("\n" + "="*50)
print("Direct execution:")

# Import and test directly
from limits.limits import safe_string

print("Attempting: safe_string(b'\\xff\\xfe')")
try:
    result = safe_string(b'\xff\xfe')
    print(f"Result: {repr(result)}")
except Exception as e:
    print(f"Exception: {type(e).__name__}: {e}")