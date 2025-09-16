"""Verify negative line_length bug in isort"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

import isort.main
from isort.settings import Config
import isort.api

# Create a test Python code string with imports
test_code = """import os
import sys
from typing import Dict, List, Optional
from collections import defaultdict, Counter
"""

print("=" * 60)
print("Verifying negative line_length behavior in isort")
print("=" * 60)

# First, check if parse_args accepts negative values
print("\n1. Testing parse_args with negative line_length:")
result = isort.main.parse_args(["--line-length", "-10"])
line_length_value = result.get('line_length')
print(f"   parse_args(['--line-length', '-10']) -> line_length = {line_length_value}")

if line_length_value is not None and line_length_value < 0:
    print("   ✗ parse_args accepts negative line_length!")
    
    # Now test if Config accepts it
    print("\n2. Testing Config with negative line_length:")
    try:
        config = Config(line_length=-10)
        print(f"   Config(line_length=-10) created successfully")
        print(f"   config.line_length = {config.line_length}")
        
        # Now test if this causes issues in actual sorting
        print("\n3. Testing actual sorting with negative line_length:")
        try:
            sorted_code = isort.api.sort_code_string(test_code, line_length=-10)
            print("   sort_code_string succeeded with negative line_length!")
            print("   Original code:")
            print(test_code)
            print("\n   Sorted code:")
            print(sorted_code)
            
            # Check if the sorting behaves oddly
            if sorted_code != test_code:
                print("\n   ✗ SERIOUS BUG: Negative line_length causes unexpected behavior!")
            else:
                print("\n   Note: Code unchanged, but negative line_length still accepted")
                
        except Exception as e:
            print(f"   sort_code_string failed: {e}")
            
    except Exception as e:
        print(f"   Config rejected negative line_length: {e}")
        print("   (parse_args accepts it but Config rejects it - inconsistency)")

# Test with zero line_length
print("\n" + "=" * 60)
print("Testing zero line_length:")
print("-" * 60)

result = isort.main.parse_args(["--line-length", "0"])
line_length_value = result.get('line_length')
print(f"parse_args(['--line-length', '0']) -> line_length = {line_length_value}")

if line_length_value == 0:
    print("✗ parse_args accepts line_length=0!")
    
    try:
        config = Config(line_length=0)
        print(f"Config(line_length=0) created successfully")
        print("✗ Config also accepts line_length=0!")
        
        # Test actual sorting
        try:
            sorted_code = isort.api.sort_code_string(test_code, line_length=0)
            print("sort_code_string succeeded with line_length=0")
            print("This likely causes wrapping issues or infinite loops")
        except Exception as e:
            print(f"sort_code_string failed with line_length=0: {e}")
            
    except Exception as e:
        print(f"Config rejected line_length=0: {e}")

# Test with negative wrap_length
print("\n" + "=" * 60)
print("Testing negative wrap_length:")
print("-" * 60)

result = isort.main.parse_args(["--wrap-length", "-5"])
wrap_length_value = result.get('wrap_length')
print(f"parse_args(['--wrap-length', '-5']) -> wrap_length = {wrap_length_value}")

if wrap_length_value is not None and wrap_length_value < 0:
    print("✗ parse_args accepts negative wrap_length!")
    
    try:
        config = Config(wrap_length=-5)
        print(f"Config(wrap_length=-5) created successfully")
        print("✗ Config accepts negative wrap_length!")
    except Exception as e:
        print(f"Config rejected negative wrap_length: {e}")

print("\n" + "=" * 60)
print("CONCLUSION:")
print("=" * 60)

if line_length_value < 0 or line_length_value == 0:
    print("\nBUG CONFIRMED: isort accepts invalid line_length values!")
    print("- Negative and zero line_length values are accepted by parse_args")
    print("- These values make no logical sense for code formatting")
    print("- This could lead to unexpected behavior or crashes in production")
else:
    print("\nNo bugs found in the tested scenarios.")