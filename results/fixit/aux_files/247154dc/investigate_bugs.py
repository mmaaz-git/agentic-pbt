#!/usr/bin/env python3
"""
Investigate the potential bugs found.
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fixit_env/lib/python3.13/site-packages')

from fixit.ftypes import QualifiedRuleRegex, LintIgnoreRegex

# Bug 1: QualifiedRuleRegex accepts identifiers starting with numbers
print("Bug 1: QualifiedRuleRegex")
print("-" * 40)

test_cases = [
    "123module",  # starts with number
    "123",  # just numbers
    "1.2.3",  # dots and numbers
]

for case in test_cases:
    match = QualifiedRuleRegex.match(case)
    print(f"Pattern: {case!r}")
    if match:
        print(f"  MATCHED: module={match.group('module')}, name={match.group('name')}")
    else:
        print(f"  No match")

# Check what the regex actually is
print(f"\nActual regex pattern:")
print(QualifiedRuleRegex.pattern)

# Bug 2: LintIgnoreRegex doesn't capture all rules properly
print("\n\nBug 2: LintIgnoreRegex")
print("-" * 40)

test_cases = [
    "#  lint-ignore:  rule1  ,rule2,  rule3  ",
    "# lint-ignore: rule1, rule2, rule3",
    "# lint-ignore: rule1  # comment",
]

for case in test_cases:
    match = LintIgnoreRegex.search(case)
    print(f"Pattern: {case!r}")
    if match:
        print(f"  MATCHED: directive={match.group(1)}, rules={match.group(2)!r}")
        print(f"  Full match: {match.group(0)!r}")
    else:
        print(f"  No match")

print(f"\nActual regex pattern:")
print(LintIgnoreRegex.pattern)