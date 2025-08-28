#!/usr/bin/env python3
"""Reproduce the bugs found in troposphere.cleanroomsml"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.cleanroomsml as crml
from troposphere import Tags

print("=" * 60)
print("BUG 1: Validation for missing required properties")
print("=" * 60)

# Create ColumnSchema without required ColumnTypes
schema = crml.ColumnSchema(
    ColumnName="test"
    # Missing required ColumnTypes!
)

print("Created ColumnSchema without required ColumnTypes field")

# Try to serialize - this SHOULD fail but doesn't
try:
    result = schema.to_dict()
    print(f"ERROR: to_dict() succeeded despite missing required field!")
    print(f"Result: {result}")
    
    # The object is in an invalid state
    print(f"schema.ColumnTypes exists: {hasattr(schema, 'ColumnTypes')}")
    print(f"Properties: {schema.properties}")
except ValueError as e:
    print(f"Correctly raised ValueError: {e}")

print("\n" + "=" * 60)
print("BUG 2: Tags round-trip serialization failure")
print("=" * 60)

# Create TrainingDataset with Tags
td = crml.TrainingDataset(
    title="TestDataset",
    Name="MyDataset",
    RoleArn="arn:aws:iam::123456789012:role/TestRole",
    TrainingData=[
        crml.Dataset(
            InputConfig=crml.DatasetInputConfig(
                DataSource=crml.DataSource(
                    GlueDataSource=crml.GlueDataSource(
                        DatabaseName="test_db",
                        TableName="test_table"
                    )
                ),
                Schema=[
                    crml.ColumnSchema(
                        ColumnName="col1",
                        ColumnTypes=["string"]
                    )
                ]
            ),
            Type="TRAINING"
        )
    ],
    Tags=Tags(Environment="Test", Project="Demo")
)

print("Created TrainingDataset with Tags")

# Serialize to dict
as_dict = td.to_dict()
print(f"Serialized successfully")
print(f"Tags in dict: {as_dict['Properties'].get('Tags')}")
print(f"Tags type: {type(as_dict['Properties'].get('Tags'))}")

# Try to reconstruct from dict - THIS FAILS
try:
    reconstructed = crml.TrainingDataset.from_dict("TestDataset", as_dict["Properties"])
    print("Successfully reconstructed from dict")
except TypeError as e:
    print(f"ERROR during reconstruction: {e}")
    print("The Tags were serialized as a list but from_dict expects a Tags object!")

print("\n" + "=" * 60)
print("BUG 1 - Additional Testing")
print("=" * 60)

# Let's see what happens with validation flag
schema2 = crml.ColumnSchema(ColumnName="test2")

# Explicitly disable validation
schema2_no_val = schema2.no_validation()
try:
    result = schema2_no_val.to_dict(validation=False)
    print(f"With validation=False: to_dict() succeeded")
    print(f"Result: {result}")
except ValueError as e:
    print(f"Even with validation=False, got error: {e}")

# Try with validation=True (default)
try:
    result = schema2.to_dict(validation=True)
    print(f"With validation=True: to_dict() succeeded")
    print(f"Result: {result}")
    print("BUG CONFIRMED: Validation doesn't catch missing required properties!")
except ValueError as e:
    print(f"Correctly raised ValueError: {e}")