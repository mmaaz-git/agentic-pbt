#!/usr/bin/env python3
"""Minimal reproductions of bugs found in packaging.specifiers"""

from packaging.specifiers import Specifier, SpecifierSet
from packaging.version import Version

print("=" * 60)
print("BUG 1: Filter/Contains Inconsistency for Prereleases")
print("=" * 60)

# Bug 1: filter() and contains() disagree on prerelease handling
spec = Specifier('!=0')
prerelease_version = '0a1'

# Using contains method
version_obj = Version(prerelease_version)
contains_result = version_obj in spec

# Using filter method
filter_result = list(spec.filter([prerelease_version]))
in_filter = prerelease_version in filter_result

print(f"Specifier: {spec}")
print(f"Version: {prerelease_version}")
print(f"contains() says version is in spec: {contains_result}")
print(f"filter() includes version: {in_filter}")
print(f"Filter result: {filter_result}")
print()
print("EXPECTED: Both methods should agree (both True or both False)")
print(f"ACTUAL: Inconsistent - contains()={contains_result}, filter()={in_filter}")
print()

print("=" * 60)
print("BUG 2: SpecifierSet Intersection Violates Set Semantics")
print("=" * 60)

# Bug 2: Intersection includes versions not in both sets
s1 = SpecifierSet('==1a1')  # Only matches 1a1
s2 = SpecifierSet('!=0')    # Should exclude prereleases by default
version = Version('1a1')

# Check membership in individual sets
in_s1 = version in s1
in_s2 = version in s2

# Check membership in intersection
intersection = s1 & s2
in_intersection = version in intersection

print(f"SpecifierSet 1: {s1}")
print(f"SpecifierSet 2: {s2}")
print(f"Intersection: {intersection}")
print(f"Version: {version}")
print()
print(f"Version in s1: {in_s1}")
print(f"Version in s2: {in_s2}")
print(f"Version in intersection: {in_intersection}")
print()
print("EXPECTED: Version should be in intersection IFF it's in BOTH s1 AND s2")
print(f"ACTUAL: Version is in intersection but not in s2!")
print()

# Additional verification
print("Testing with more versions to show the pattern:")
test_versions = ['1a1', '1b1', '1rc1', '1', '2a1', '2']
for v_str in test_versions:
    v = Version(v_str)
    result = f"  {v_str}: in_s1={v in s1}, in_s2={v in s2}, in_intersection={v in intersection}"
    print(result)