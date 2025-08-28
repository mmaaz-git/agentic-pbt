"""Minimal reproduction of the LookupDict bug."""
import requests.status_codes

# Create a LookupDict instance
codes = requests.status_codes.codes

# The bug: inherited dict methods are inconsistently accessed
print("Accessing 'clear' method:")
print(f"codes['clear'] = {codes['clear']}")  # Returns None
print(f"codes.clear = {codes.clear}")  # Returns the actual method

# This violates the expectation that obj[key] == getattr(obj, key)
assert codes['clear'] == getattr(codes, 'clear'), "Inconsistent access!"