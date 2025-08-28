import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

import isort.main

# Direct test: parse_args with negative line_length
print("Testing parse_args with negative line_length...")
result = isort.main.parse_args(["--line-length", "-10"])
print(f"Result: {result}")
print(f"line_length value: {result.get('line_length')}")

# Check the type
if 'line_length' in result:
    print(f"Type of line_length: {type(result['line_length'])}")
    print(f"Value is negative: {result['line_length'] < 0}")
    
    # This is potentially a bug - negative line_length doesn't make sense
    if result['line_length'] < 0:
        print("\nPOTENTIAL BUG FOUND:")
        print("parse_args accepts negative line_length values!")
        print("A negative line_length doesn't make logical sense for formatting.")