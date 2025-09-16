#!/usr/bin/env python
"""Minimal reproduction of potential bugs in troposphere.finspace"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

# Test 1: Empty string title bug
print("Testing empty string as title...")
try:
    import troposphere.finspace as finspace
    env = finspace.Environment("", Name="TestEnv")
    print(f"BUG CONFIRMED: Empty string accepted as title!")
    print(f"Environment title is: '{env.title}'")
    
    # Check if it validates
    try:
        result = env.to_dict()
        print(f"Empty title passes validation and creates dict: {result}")
    except Exception as e:
        print(f"Validation fails with: {e}")
except ValueError as e:
    print(f"Empty string correctly rejected: {e}")

print("\n" + "="*50 + "\n")

# Test 2: None title handling
print("Testing None as title...")
try:
    import troposphere.finspace as finspace
    env = finspace.Environment(None, Name="TestEnv")
    print(f"Environment created with None title: {env.title}")
    
    # Check validation
    try:
        result = env.to_dict()
        if env.title is None:
            print(f"BUG CONFIRMED: None title passes validation!")
            print(f"Result Type: {result.get('Type')}")
    except AttributeError as e:
        print(f"AttributeError during validation: {e}")
        print("This indicates None causes issues in validation")
    except Exception as e:
        print(f"Other error: {type(e).__name__}: {e}")
        
except (TypeError, ValueError) as e:
    print(f"None correctly causes error: {e}")

print("\n" + "="*50 + "\n")

# Test 3: Whitespace bypass
print("Testing whitespace characters...")
test_cases = [" ", "  ", "\t", "\n", "\r"]
for ws in test_cases:
    try:
        import troposphere.finspace as finspace
        env = finspace.Environment(ws, Name="TestEnv")
        print(f"BUG CONFIRMED: Whitespace {repr(ws)} accepted as title!")
    except ValueError as e:
        if "not alphanumeric" in str(e):
            print(f"OK: Whitespace {repr(ws)} rejected")
        else:
            print(f"Unexpected error for {repr(ws)}: {e}")

print("\n" + "="*50 + "\n")

# Test 4: Unicode characters
print("Testing Unicode characters...")
unicode_tests = ["Test🦄", "Тест", "测试", "Café"]
for title in unicode_tests:
    try:
        import troposphere.finspace as finspace
        env = finspace.Environment(title, Name="TestEnv")
        print(f"BUG CONFIRMED: Unicode title {repr(title)} accepted!")
    except ValueError as e:
        if "not alphanumeric" in str(e):
            print(f"OK: Unicode {repr(title)} rejected")
        else:
            print(f"Unexpected error for {repr(title)}: {e}")

print("\n" + "="*50)
print("Reproduction test complete")