#!/usr/bin/env python3
"""Direct testing of parse_vars to find bugs."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from pyramid.scripts.common import parse_vars

print("Looking for bugs in parse_vars...")
print("=" * 60)

# Test collection
bugs_found = []

def test_case(description, input_list, expected=None, should_error=False):
    """Run a test case and report results."""
    print(f"\nTest: {description}")
    print(f"Input: {repr(input_list)}")
    
    try:
        result = parse_vars(input_list)
        print(f"Result: {result}")
        
        if should_error:
            bugs_found.append(f"Should have raised error for: {input_list}")
            print("✗ BUG: Should have raised ValueError")
            return False
        
        if expected is not None and result != expected:
            bugs_found.append(f"Wrong result for {input_list}: got {result}, expected {expected}")
            print(f"✗ BUG: Expected {expected}")
            return False
            
        print("✓ PASS")
        return True
        
    except ValueError as e:
        print(f"ValueError: {e}")
        
        if not should_error:
            bugs_found.append(f"Unexpected error for {input_list}: {e}")
            print("✗ BUG: Unexpected ValueError")
            return False
            
        print("✓ PASS (correctly raised error)")
        return True
        
    except Exception as e:
        bugs_found.append(f"Unexpected exception for {input_list}: {type(e).__name__}: {e}")
        print(f"✗ BUG: Unexpected {type(e).__name__}: {e}")
        return False

# Basic functionality tests
print("\n--- BASIC TESTS ---")
test_case("Simple assignment", ["a=b"], {"a": "b"})
test_case("Multiple assignments", ["a=1", "b=2"], {"a": "1", "b": "2"})
test_case("Empty value", ["key="], {"key": ""})
test_case("Empty key", ["=value"], {"": "value"})
test_case("Just equals", ["="], {"": ""})
test_case("Multiple equals in value", ["key=val=ue"], {"key": "val=ue"})
test_case("Many equals in value", ["k=a=b=c=d"], {"k": "a=b=c=d"})

# Error cases
print("\n--- ERROR CASES ---")
test_case("No equals", ["noequals"], should_error=True)
test_case("Empty string", [""], should_error=True)
test_case("Multiple items, one bad", ["a=1", "bad", "b=2"], should_error=True)

# Edge cases
print("\n--- EDGE CASES ---")
test_case("Whitespace key", [" =value"], {" ": "value"})
test_case("Whitespace value", ["key= "], {"key": " "})
test_case("Tab key", ["\t=value"], {"\t": "value"})
test_case("Newline in value", ["key=line1\nline2"], {"key": "line1\nline2"})
test_case("Unicode", ["🦄=🎉"], {"🦄": "🎉"})
test_case("Null byte in value", ["key=val\x00ue"], {"key": "val\x00ue"})

# Duplicate keys
print("\n--- DUPLICATE KEYS ---")
test_case("Duplicate key - last wins", ["key=first", "key=second"], {"key": "second"})
test_case("Multiple duplicates", ["a=1", "b=2", "a=3", "b=4"], {"a": "3", "b": "4"})

# Special patterns
print("\n--- SPECIAL PATTERNS ---")
test_case("Proto pollution attempt", ["__proto__=value"], {"__proto__": "value"})
test_case("Constructor", ["constructor=value"], {"constructor": "value"})
test_case("Shell substitution syntax", ["key=${value}"], {"key": "${value}"})
test_case("Command substitution", ["key=$(cmd)"], {"key": "$(cmd)"})
test_case("Format string", ["key=%(var)s"], {"key": "%(var)s"})

# Complex values
print("\n--- COMPLEX VALUES ---")
test_case("JSON-like value", ['key={"a": "b"}'], {"key": '{"a": "b"}'})
test_case("URL value", ["url=http://example.com?a=1&b=2"], {"url": "http://example.com?a=1&b=2"})
test_case("Path value", ["path=/usr/bin/python=test"], {"path": "/usr/bin/python=test"})

# Very long strings
print("\n--- STRESS TESTS ---")
long_key = "k" * 1000
long_value = "v" * 10000
test_case("Long key and value", [f"{long_key}={long_value}"], {long_key: long_value})

# Multiple equals at boundaries
print("\n--- EQUALS BOUNDARIES ---")
test_case("Value starts with equals", ["key==value"], {"key": "=value"})
test_case("Value is all equals", ["key===="], {"key": "==="})
test_case("Key ends with special char", ["key-=value"], {"key-": "value"})

# Summary
print("\n" + "=" * 60)
print("TESTING COMPLETE")
print("=" * 60)

if bugs_found:
    print(f"\n❌ BUGS FOUND ({len(bugs_found)}):")
    for bug in bugs_found:
        print(f"  - {bug}")
else:
    print("\n✅ NO BUGS FOUND - All tests passed!")