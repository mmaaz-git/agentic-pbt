#!/usr/bin/env venv/bin/python
import troposphere.lakeformation as lf
import troposphere
import inspect
import sys

# Import all classes for detailed exploration
from troposphere.lakeformation import *
from troposphere import AWSObject, AWSProperty

print("=== Understanding AWSObject and AWSProperty ===")
print(f"AWSObject type: {type(AWSObject)}")
print(f"AWSProperty type: {type(AWSProperty)}")

# Explore base classes
print("\n=== AWSObject Methods ===")
for name, method in inspect.getmembers(AWSObject, inspect.isfunction):
    if not name.startswith('_'):
        sig = inspect.signature(method) if hasattr(method, '__func__') else "N/A"
        print(f"  {name}{sig}")

print("\n=== AWSProperty Methods ===")
for name, method in inspect.getmembers(AWSProperty, inspect.isfunction):
    if not name.startswith('_'):
        sig = inspect.signature(method) if hasattr(method, '__func__') else "N/A"
        print(f"  {name}{sig}")

# Check the boolean validator
print("\n=== Boolean validator ===")
print(f"boolean function: {boolean}")
print(f"boolean signature: {inspect.signature(boolean)}")
print(f"boolean source:\n{inspect.getsource(boolean)}")

# Let's test creation of some classes
print("\n=== Testing class instantiation ===")
try:
    # Create a simple property with no required fields
    cw = ColumnWildcard(ExcludedColumnNames=["col1", "col2"])
    print(f"ColumnWildcard created: {cw}")
    print(f"ColumnWildcard dict: {cw.to_dict()}")
except Exception as e:
    print(f"Error creating ColumnWildcard: {e}")

try:
    # Create a DataLakePrincipal
    dlp = DataLakePrincipal(DataLakePrincipalIdentifier="arn:aws:iam::123456789012:role/MyRole")
    print(f"DataLakePrincipal created: {dlp}")
    print(f"DataLakePrincipal dict: {dlp.to_dict()}")
except Exception as e:
    print(f"Error creating DataLakePrincipal: {e}")

# Explore validation patterns
print("\n=== Exploring property definitions ===")
print(f"DataLakeSettings.props: {DataLakeSettings.props}")
print(f"\nResource.props: {Resource.props}")