"""Minimal reproduction of SpecifierSet prerelease handling bug."""

import packaging.version
import packaging.specifiers

# The bug: Combined specifiers don't properly enforce AND logic for prereleases

version = packaging.version.Version('1a0')  # A prerelease version

# Individual specifiers
spec1 = packaging.specifiers.SpecifierSet('>=0')
spec2 = packaging.specifiers.SpecifierSet('>=0a0')

# Combined specifier
combined = packaging.specifiers.SpecifierSet('>=0,>=0a0')

# Check membership
print(f"Version {version} in '>=0': {version in spec1}")  # False (prereleases excluded by default)
print(f"Version {version} in '>=0a0': {version in spec2}")  # True (prerelease explicitly included)
print(f"Version {version} in '>=0,>=0a0': {version in combined}")  # True (BUG!)

# The bug: Since >=0 excludes prereleases when evaluated alone,
# and the combined specifier should satisfy BOTH conditions (AND logic),
# the result should be False, not True.

print("\nExpected: False (must satisfy both conditions)")
print(f"Actual: {version in combined}")
print(f"Bug: {(version in combined) != ((version in spec1) and (version in spec2))}")