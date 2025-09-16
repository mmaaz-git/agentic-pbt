#!/usr/bin/env python3
"""Final comprehensive testing for pyct.report bugs"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyct_env/lib/python3.13/site-packages')

import io
from pyct.report import report

print("Final Bug Confirmation for pyct.report")
print("=" * 70)

# Bug 1: Output format ambiguity with ' # ' in package names
print("\n1. Testing output format ambiguity bug...")
print("-" * 40)

ambiguous_inputs = [
    "package # comment",
    "test # another # test",
    " # ",
    "# # #",
    "foo # bar # baz",
]

for package_name in ambiguous_inputs:
    captured_output = io.StringIO()
    sys.stdout = captured_output
    try:
        report(package_name)
    finally:
        sys.stdout = sys.__stdout__
    
    output = captured_output.getvalue().strip()
    parts = output.split(' # ')
    
    if len(parts) != 2:
        print(f"✗ BUG CONFIRMED: Ambiguous output!")
        print(f"  Input: '{package_name}'")
        print(f"  Output: '{output}'")
        print(f"  Split into {len(parts)} parts instead of 2:")
        for i, part in enumerate(parts):
            print(f"    Part {i}: '{part}'")
        print()

# Bug 2: Newline handling
print("\n2. Testing newline handling...")
print("-" * 40)

newline_test = "package\nname"
captured_output = io.StringIO()
sys.stdout = captured_output
try:
    report(newline_test)
finally:
    sys.stdout = sys.__stdout__

output = captured_output.getvalue()
lines = output.strip().split('\n')

if len(lines) > 1:
    print(f"✗ ISSUE: Newline in package name produces multi-line output")
    print(f"  Input (repr): {repr(newline_test)}")
    print(f"  Output has {len(lines)} lines:")
    for i, line in enumerate(lines):
        print(f"    Line {i}: '{line}'")
    print(f"  This may break tools that expect one line per package")
else:
    print("✓ Newlines handled in single line")

print("\n" + "=" * 70)
print("\nBUG TRIAGE:")
print("-" * 40)

print("\n1. Output Format Ambiguity Bug:")
print("   - Legitimacy: YES - This is a real parsing issue")
print("   - Impact: Tools parsing the output cannot reliably separate package info from location")
print("   - Severity: MEDIUM - API contract violation for output parsing")
print("   - Bug Type: Contract - Output format differs from expected parseable structure")

print("\n2. Newline Handling:")
print("   - Legitimacy: MARGINAL - Package names with newlines are unusual")
print("   - Impact: Could break tools expecting one line per package")
print("   - Severity: LOW - Edge case with uncommon input")
print("   - Bug Type: Contract - Multi-line output when single line expected")

print("\n" + "=" * 70)
print("\nCONCLUSION: Found 1 genuine bug worth reporting (output format ambiguity)")