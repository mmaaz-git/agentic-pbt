"""Simple reproducers for potential bugs in isort.main"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

import isort.main
from isort.settings import Config

print("Testing for negative line_length bug...")
print("-" * 40)

# Test 1: parse_args accepts negative line_length
print("1. Testing: isort.main.parse_args(['--line-length', '-10'])")
result = isort.main.parse_args(["--line-length", "-10"])
print(f"   Result: {result}")
print(f"   line_length value: {result.get('line_length')}")

if result.get('line_length', 0) < 0:
    print("\n   *** BUG FOUND ***")
    print("   parse_args accepts negative line_length!")
    print("   This is illogical as line length cannot be negative.")
    
    # Test if Config also accepts it
    print("\n2. Testing: Config(line_length=-10)")
    try:
        config = Config(line_length=-10)
        print(f"   Config created with line_length={config.line_length}")
        print("   *** SEVERE BUG: Config also accepts negative line_length! ***")
    except Exception as e:
        print(f"   Config rejected it with: {e}")

print("\n" + "=" * 50)
print("Testing for zero line_length...")
print("-" * 40)

print("3. Testing: isort.main.parse_args(['--line-length', '0'])")
result = isort.main.parse_args(["--line-length", "0"])
print(f"   Result: {result}")
print(f"   line_length value: {result.get('line_length')}")

if result.get('line_length') == 0:
    print("\n   *** ISSUE FOUND ***")
    print("   parse_args accepts line_length=0!")
    print("   This makes no logical sense for formatting.")
    
    # Test if Config accepts it
    print("\n4. Testing: Config(line_length=0)")
    try:
        config = Config(line_length=0)
        print(f"   Config created with line_length={config.line_length}")
        print("   *** Config also accepts line_length=0! ***")
    except Exception as e:
        print(f"   Config rejected it with: {e}")