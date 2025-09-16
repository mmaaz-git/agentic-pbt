import sys
sys.path.insert(0, './venv/lib/python3.13/site-packages')

import troposphere.lakeformation as lf
import troposphere
import inspect

# Import all classes for detailed exploration
from troposphere.lakeformation import *
from troposphere import AWSObject, AWSProperty
from troposphere.validators import boolean

print("=== Understanding AWSObject and AWSProperty ===")
print(f"AWSObject type: {type(AWSObject)}")
print(f"AWSProperty type: {type(AWSProperty)}")

# Explore base classes
print("\n=== AWSObject Methods ===")
for name, method in inspect.getmembers(AWSObject):
    if not name.startswith('_') and callable(method):
        print(f"  {name}")

print("\n=== AWSProperty Methods ===")
for name, method in inspect.getmembers(AWSProperty):
    if not name.startswith('_') and callable(method):
        print(f"  {name}")

# Check the boolean validator
print("\n=== Boolean validator ===")
print(f"boolean function: {boolean}")
try:
    print(f"boolean signature: {inspect.signature(boolean)}")
    print(f"boolean source:\n{inspect.getsource(boolean)}")
except:
    pass

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
print(f"DataLakeSettings.props keys: {list(DataLakeSettings.props.keys())}")
print(f"Resource.props keys: {list(Resource.props.keys())}")

# Check prop types
print("\n=== Prop type patterns ===")
for key, value in Resource.props.items():
    print(f"  {key}: {value}")