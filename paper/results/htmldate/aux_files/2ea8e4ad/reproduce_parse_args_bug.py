"""Reproduction script for parse_args bug"""
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/htmldate_env/lib/python3.13/site-packages')

# Simulate running with pytest arguments
old_argv = sys.argv
sys.argv = ["pytest", "test_file.py", "--tb=short"]

from htmldate.cli import parse_args

print(f"Current sys.argv: {sys.argv}")
print("\nCalling parse_args([]) - should parse empty list, not sys.argv")
try:
    args = parse_args([])
    print(f"Success: Got args")
except SystemExit as e:
    print(f"BUG: SystemExit raised - parse_args ignores its parameter and uses sys.argv instead")
    print("The function should use the provided args parameter, not sys.argv")
    
# Restore
sys.argv = old_argv