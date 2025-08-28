#!/usr/bin/env python3
"""
Test the actual impact of the QualifiedRuleRegex bug
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fixit_env/lib/python3.13/site-packages')

from pathlib import Path
from fixit.config import find_rules, parse_rule
from fixit.ftypes import QualifiedRule

print("Testing the actual impact of accepting invalid module names")
print("=" * 60)

# Test 1: What happens when we try to use find_rules with an invalid module name?
print("\nTest 1: Using find_rules with '123module'")
print("-" * 40)
invalid_rule = QualifiedRule(module="123module")
try:
    rules = list(find_rules(invalid_rule))
    print(f"Unexpectedly succeeded: {rules}")
except Exception as e:
    print(f"✓ Failed as expected: {type(e).__name__}: {e}")

# Test 2: What happens with parse_rule and find_rules together?
print("\nTest 2: Using parse_rule + find_rules with '999invalid'")
print("-" * 40)
try:
    parsed = parse_rule("999invalid", Path.cwd())
    print(f"parse_rule succeeded: {parsed}")
    rules = list(find_rules(parsed))
    print(f"find_rules unexpectedly succeeded: {rules}")
except Exception as e:
    print(f"✓ Failed as expected: {type(e).__name__}: {e}")

# Test 3: Compare with a valid module name
print("\nTest 3: Valid module 'fixit.rules' for comparison")
print("-" * 40)
try:
    valid_rule = parse_rule("fixit.rules", Path.cwd())
    print(f"parse_rule succeeded: {valid_rule}")
    rules = list(find_rules(valid_rule))
    print(f"✓ find_rules found {len(rules)} rules")
except Exception as e:
    print(f"Unexpected error: {e}")

print("\nConclusion:")
print("-" * 40)
print("The bug allows invalid module names to pass validation,")
print("but they will fail later when trying to import them.")
print("This violates the fail-fast principle and gives confusing error messages.")