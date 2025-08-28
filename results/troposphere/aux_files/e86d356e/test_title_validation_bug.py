#!/usr/bin/env python3
"""Test for title validation edge cases."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.cassandra as cassandra
from hypothesis import given, strategies as st


# Test various title edge cases
test_cases = [
    ("", "empty string"),
    (None, "None"),
    ("valid123", "alphanumeric"),
    ("has-dash", "with dash"),
    ("has_underscore", "with underscore"),
    ("has space", "with space"),
    ("123start", "starts with number"),
    (":", "colon only"),
    ("CamelCase", "camel case"),
    ("UPPERCASE", "uppercase"),
    ("lowercase", "lowercase"),
    (".", "period"),
    ("/", "slash"),
    ("resource/name", "with slash"),
    ("my-resource", "kebab-case"),
    ("my_resource", "snake_case"),
]

print("Testing title validation:")
print("=" * 50)

for title, description in test_cases:
    try:
        # Test with Keyspace
        keyspace = cassandra.Keyspace(
            title=title,
            KeyspaceName="test"
        )
        print(f"✓ Accepted {description:20} title={repr(title)}")
    except ValueError as e:
        if "not alphanumeric" in str(e):
            print(f"✗ Rejected {description:20} title={repr(title)}")
        else:
            print(f"? Error for {description:20} title={repr(title)}: {e}")
    except TypeError as e:
        print(f"? TypeError for {description:20} title={repr(title)}: {e}")


print("\n" + "=" * 50)
print("Testing AWSProperty (Column) which has optional title:")
print("=" * 50)

# Column is an AWSProperty which has optional title
for title, description in test_cases:
    try:
        column = cassandra.Column(
            title=title,  # Optional for AWSProperty
            ColumnName="test",
            ColumnType="text"
        )
        print(f"✓ Accepted {description:20} title={repr(title)}")
    except ValueError as e:
        if "not alphanumeric" in str(e):
            print(f"✗ Rejected {description:20} title={repr(title)}")
        else:
            print(f"? Error for {description:20} title={repr(title)}: {e}")
    except TypeError as e:
        print(f"? TypeError for {description:20} title={repr(title)}: {e}")


# Property-based test for title validation
@given(st.text())
def test_title_validation_consistency(title):
    """Title validation should be consistent and predictable."""
    is_valid = title and title.replace('_', '').replace('-', '').isalnum()
    
    # Test with AWSObject (requires title)
    if title is not None:
        try:
            keyspace = cassandra.Keyspace(
                title=title,
                KeyspaceName="test"
            )
            # If accepted, should match our prediction
            actual_valid = True
        except ValueError as e:
            if "not alphanumeric" in str(e):
                actual_valid = False
            else:
                raise
        
        # Check if our prediction matches
        if is_valid != actual_valid:
            print(f"\nInconsistency: title={repr(title)}")
            print(f"  Expected valid={is_valid}, actual valid={actual_valid}")


print("\n" + "=" * 50)
print("ANALYSIS:")
print("=" * 50)
print("The title validation regex is: ^[a-zA-Z0-9]+$")
print("This means:")
print("1. No empty strings")
print("2. No special characters (not even underscore or dash)")
print("3. No spaces")
print("4. Only letters and numbers")
print("")
print("This is quite restrictive for CloudFormation resource names,")
print("which often use dashes, underscores, or other separators.")
print("")
print("Additionally, AWSProperty objects have optional titles but")
print("still validate them when provided, even though None is allowed.")