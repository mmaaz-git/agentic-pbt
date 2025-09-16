#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/cloudscraper_env/lib/python3.13/site-packages')

from cloudscraper.interpreters.jsunfuck import jsunfuck, MAPPING, SIMPLE
from cloudscraper.interpreters.encapsulated import template

print("Testing cloudscraper.interpreters for bugs...")
print("=" * 60)

# Bug Hunt 1: Check for replacement order issues
print("\n1. Testing jsunfuck replacement order...")
bugs_found = []

# Check if any MAPPING value contains another MAPPING value
for key1, pattern1 in MAPPING.items():
    for key2, pattern2 in MAPPING.items():
        if key1 != key2 and pattern1 in pattern2:
            # This could be problematic if not handled correctly
            test_input = pattern2
            result = jsunfuck(test_input)
            expected = f'"{key2}"'
            if result != expected:
                bugs_found.append(f"Pattern overlap bug: {key2} pattern contains {key1} pattern")
                print(f"  BUG: Pattern for '{key2}' contains pattern for '{key1}'")
                print(f"       Input: {pattern2[:50]}...")
                print(f"       Expected: {expected}")
                print(f"       Got: {result}")

# Bug Hunt 2: Check for infinite loop potential
print("\n2. Testing for infinite loop potential...")

# Check if any replacement could create a pattern
for key, pattern in MAPPING.items():
    replacement = f'"{key}"'
    for other_pattern in MAPPING.values():
        if other_pattern in replacement:
            bugs_found.append(f"Potential infinite loop: replacing {pattern} with {replacement} creates {other_pattern}")
            print(f"  POTENTIAL BUG: Replacement '{replacement}' contains pattern {other_pattern[:30]}...")

# Bug Hunt 3: Test idempotence with mixed patterns
print("\n3. Testing idempotence with mixed patterns...")

test_cases = [
    # Mix of MAPPING and SIMPLE patterns
    SIMPLE['false'] + MAPPING['a'] + SIMPLE['true'],
    # Multiple same patterns
    MAPPING['a'] * 5,
    # Pattern that looks like it could be recursive
    '(false+"")[1](false+"")[1]',
]

for test_input in test_cases:
    once = jsunfuck(test_input)
    twice = jsunfuck(once)
    if once != twice:
        bugs_found.append(f"Idempotence violation: {test_input[:50]}...")
        print(f"  BUG: Not idempotent for input: {test_input[:50]}...")
        print(f"       First:  {once[:50]}...")
        print(f"       Second: {twice[:50]}...")

# Bug Hunt 4: Template function edge cases
print("\n4. Testing template function edge cases...")

# Test with empty k value
edge_case_1 = '''
<script>
setTimeout(function(){
    var k = '';
    a.value = something.toFixed(10);
}, 4000);
</script>
'''

try:
    result = template(edge_case_1, "example.com")
    print(f"  Edge case (empty k): Passed")
except Exception as e:
    print(f"  Edge case (empty k): {e}")

# Test with special characters in k
edge_case_2 = '''
<script>
setTimeout(function(){
    var k = '../../etc/passwd';
    a.value = something.toFixed(10);
}, 4000);
</script>
<div id="../../etc/passwd001">malicious</div>
'''

try:
    result = template(edge_case_2, "example.com")
    if '../../etc/passwd' in result:
        print(f"  WARNING: Path traversal pattern in result")
except Exception as e:
    print(f"  Edge case (path in k): {e}")

# Test with regex special chars in domain
special_domains = ["exam{ple}.com", "test[123].com", "site(1).com"]
base_body = '''
<script>
setTimeout(function(){
    var k = 'key';
    a.value = something.toFixed(10);
}, 4000);
</script>
'''

for domain in special_domains:
    try:
        result = template(base_body, domain)
        # Check if domain is properly handled
        if '{' in domain and '}' in domain:
            # Could cause issues with string formatting
            print(f"  WARNING: Domain with braces '{domain}' processed")
    except Exception as e:
        if 'Unable to identify' not in str(e):
            print(f"  Unexpected error with domain '{domain}': {e}")

# Bug Hunt 5: Check SIMPLE patterns for issues
print("\n5. Testing SIMPLE patterns...")

for key, pattern in SIMPLE.items():
    # Check if the pattern itself would be replaced by MAPPING
    for mapping_pattern in MAPPING.values():
        if mapping_pattern in pattern:
            print(f"  WARNING: SIMPLE['{key}'] contains MAPPING pattern")
            bugs_found.append(f"SIMPLE pattern '{key}' contains MAPPING pattern")

# Summary
print("\n" + "=" * 60)
if bugs_found:
    print(f"FOUND {len(bugs_found)} POTENTIAL ISSUES:")
    for i, bug in enumerate(bugs_found, 1):
        print(f"  {i}. {bug}")
else:
    print("NO BUGS FOUND - All tests passed ✅")

print("\n" + "=" * 60)