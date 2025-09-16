#!/usr/bin/env python3
"""Investigate the title validation bug"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.cleanroomsml as crml
import troposphere
import re

# Check the validation regex
print("Validation regex pattern:", troposphere.valid_names.pattern)

# Test specific character
test_char = "µ"
print(f"\nTesting character: '{test_char}'")
print(f"Is alphanumeric (Python): {test_char.isalnum()}")
print(f"Matches regex: {bool(troposphere.valid_names.match(test_char))}")
print(f"Unicode category: {test_char}")
print(f"Unicode name: {test_char!r}")

# Test a few more Unicode letters
test_chars = ["µ", "ñ", "ü", "Ω", "λ", "π", "α", "β", "γ"]
print("\nTesting various Unicode characters:")
for char in test_chars:
    py_alnum = char.isalnum()
    regex_match = bool(troposphere.valid_names.match(char))
    print(f"  '{char}': Python isalnum={py_alnum}, Regex match={regex_match}")

# The bug: Python's isalnum() returns True for Unicode letters,
# but the regex ^[a-zA-Z0-9]+$ only matches ASCII alphanumeric

# Minimal reproduction
print("\n--- Minimal Reproduction ---")
try:
    dataset = crml.Dataset(
        InputConfig=crml.DatasetInputConfig(
            DataSource=crml.DataSource(
                GlueDataSource=crml.GlueDataSource(
                    DatabaseName="db",
                    TableName="table"
                )
            ),
            Schema=[
                crml.ColumnSchema(
                    ColumnName="col",
                    ColumnTypes=["string"]
                )
            ]
        ),
        Type="TRAINING"
    )
    
    # This should fail
    td = crml.TrainingDataset(
        title="µ",  # Unicode letter that Python considers alphanumeric
        Name="TestDataset",
        RoleArn="arn:aws:iam::123456789012:role/TestRole",
        TrainingData=[dataset]
    )
    print("ERROR: Should have raised ValueError!")
except ValueError as e:
    print(f"Correctly raised ValueError: {e}")

# The issue is in the BaseAWSObject.validate_title() method
# which uses: valid_names = re.compile(r"^[a-zA-Z0-9]+$")
# This only accepts ASCII alphanumeric, not Unicode alphanumeric