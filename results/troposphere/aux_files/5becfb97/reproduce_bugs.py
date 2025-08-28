#!/usr/bin/env python3
import sys
sys.path.insert(0, './venv/lib/python3.13/site-packages')

print("=== Bug 1: Boolean validator case-sensitivity ===")
from troposphere.validators import boolean

# Test case variations
test_cases = [
    ("true", "lowercase"),
    ("True", "Title case"),
    ("TRUE", "UPPERCASE"),
    ("false", "lowercase"),
    ("False", "Title case"),
    ("FALSE", "UPPERCASE"),
]

for value, description in test_cases:
    try:
        result = boolean(value)
        print(f"✓ boolean('{value}') = {result} ({description})")
    except ValueError:
        print(f"✗ boolean('{value}') = ValueError ({description})")

print("\nImpact: Inconsistent handling of case variations violates user expectations")
print("Expected: All case variations of 'true'/'false' should work consistently")

print("\n=== Bug 2: from_dict round-trip failure ===")
from troposphere.lakeformation import DataCellsFilter

# Create a valid DataCellsFilter
dcf = DataCellsFilter(
    "MyFilter",
    DatabaseName="mydb",
    Name="myfilter",
    TableCatalogId="12345",
    TableName="mytable"
)

# Convert to dict
dict_repr = dcf.to_dict()
print(f"Original to_dict(): {dict_repr}")

# Try to reconstruct
try:
    reconstructed = DataCellsFilter.from_dict("MyFilter2", dict_repr)
    print(f"✓ from_dict succeeded")
except AttributeError as e:
    print(f"✗ from_dict failed: {e}")

print("\nImpact: Round-trip operations don't work, breaking serialization/deserialization")
print("Expected: from_dict should handle the output of to_dict")

print("\n=== Bug 3: Title validation accepts invalid characters ===")
from troposphere.lakeformation import Resource

# Test with a superscript character that passes initial check but fails validation
test_titles = [
    "ValidTitle123",    # Should work
    "¹SuperScript",     # Passes isalnum() but fails regex
    "Test-With-Dash",   # Should fail (has dashes)
]

for title in test_titles:
    try:
        # Check if it passes the assume filter
        is_alnum = title.replace(" ", "").isalnum()
        
        # Try to create resource
        resource = Resource(
            title,
            ResourceArn="arn:aws:s3:::mybucket",
            UseServiceLinkedRole=True
        )
        print(f"✓ Title '{title}' accepted (isalnum={is_alnum})")
    except ValueError as e:
        print(f"✗ Title '{title}' rejected: {e} (isalnum={title.replace(' ', '').isalnum()})")

print("\nImpact: Unicode characters that pass isalnum() but fail the regex validation")
print("Expected: Consistent validation - either accept all alphanumeric or be more specific")