#!/usr/bin/env python3
"""
Reproduce Bug 1: QualifiedRuleRegex accepts invalid Python module names
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fixit_env/lib/python3.13/site-packages')

from pathlib import Path
from fixit.config import parse_rule
from fixit.ftypes import QualifiedRuleRegex

# These module names start with numbers, which is invalid for Python
invalid_module_names = [
    "123module",
    "123",
    "9rules",
    "1.2.3",
    "99bottles",
]

print("Bug reproduction: QualifiedRuleRegex accepts invalid Python module names")
print("=" * 70)
print()

print("Testing QualifiedRuleRegex directly:")
print("-" * 40)
for name in invalid_module_names:
    match = QualifiedRuleRegex.match(name)
    if match:
        print(f"❌ INCORRECTLY ACCEPTED: {name!r}")
        print(f"   Module: {match.group('module')}, Name: {match.group('name')}")
    else:
        print(f"✓ Correctly rejected: {name!r}")

print()
print("Testing parse_rule function:")
print("-" * 40)
for name in invalid_module_names:
    try:
        rule = parse_rule(name, Path.cwd())
        print(f"❌ INCORRECTLY ACCEPTED: {name!r} -> {rule}")
    except Exception as e:
        print(f"✓ Correctly rejected {name!r}: {e}")

print()
print("Demonstrating the problem:")
print("-" * 40)
print("Python identifiers cannot start with digits:")
try:
    exec("import 123module")
    print("This should not happen!")
except SyntaxError as e:
    print(f"✓ Python correctly rejects '123module': {e}")

print()
print("But fixit's QualifiedRuleRegex accepts it:")
match = QualifiedRuleRegex.match("123module")
print(f"❌ QualifiedRuleRegex.match('123module') = {match}")
print(f"   This would cause problems when trying to import the module!")

print()
print("Expected behavior:")
print("-" * 40)
print("The regex should use [a-zA-Z_] for the first character, not [a-zA-Z0-9_]")
print("Python identifiers must match: [a-zA-Z_][a-zA-Z0-9_]*")