"""Test to investigate parse_args issue"""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/htmldate_env/lib/python3.13/site-packages')

from htmldate.cli import parse_args

# Test 1: Check if parse_args accepts a list of arguments
print("Test 1: parse_args with explicit argument list")
try:
    args = parse_args(["--fast"])
    print(f"Success: fast={args.fast}")
except Exception as e:
    print(f"Error: {e}")

# Test 2: What happens with invalid arguments?
print("\nTest 2: parse_args with invalid argument")
try:
    args = parse_args(["--invalid-arg"])
    print(f"Success (unexpected)")
except SystemExit as e:
    print(f"SystemExit raised (expected for invalid args)")
    
# Test 3: Empty args
print("\nTest 3: parse_args with empty list")
try:
    args = parse_args([])
    print(f"Success: fast={args.fast}, original={args.original}")
except Exception as e:
    print(f"Error: {e}")