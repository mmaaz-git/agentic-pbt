import sys
sys.path.insert(0, './venv/lib/python3.13/site-packages')

import troposphere.lakeformation as lf
from troposphere.lakeformation import *
from troposphere import AWSObject, AWSProperty
from troposphere.validators import boolean
import inspect

print("=== Analyzing potential properties to test ===\n")

# 1. Boolean validator properties
print("1. Boolean validator:")
print(f"   - Source: {inspect.getsource(boolean).strip()}")
print("   - Property: Should consistently convert same values to boolean")
print("   - Property: Should raise ValueError for invalid inputs")
print("")

# 2. to_dict/from_dict round-trip
print("2. Round-trip properties:")
for name, cls in inspect.getmembers(lf, inspect.isclass):
    if issubclass(cls, (AWSObject, AWSProperty)) and hasattr(cls, 'from_dict'):
        print(f"   - {name} has from_dict method - potential round-trip property")
        break
else:
    print("   - No classes found with from_dict method")

# Check if from_dict exists
print(f"   - AWSObject has from_dict: {hasattr(AWSObject, 'from_dict')}")
print(f"   - AWSProperty has from_dict: {hasattr(AWSProperty, 'from_dict')}")
print("")

# 3. Required field validation
print("3. Required field validation:")
for name, cls in inspect.getmembers(lf, inspect.isclass):
    if hasattr(cls, 'props'):
        required_fields = [(k, v) for k, v in cls.props.items() if v[1] == True]
        if required_fields:
            print(f"   - {name} has required fields: {[f[0] for f in required_fields]}")
            if len(required_fields) > 0:
                print(f"      Property: Should raise ValueError if required fields are missing")
            break

print("")

# 4. Type validation
print("4. Type validation properties:")
print("   - Classes with boolean validators should accept boolean-like values")
print("   - Classes with string fields should reject non-strings")
print("   - Classes with list fields should reject non-lists")
print("")

# 5. Specific class behaviors
print("5. Specific behaviors to test:")
print("   - ColumnWildcard: ExcludedColumnNames should be a list of strings")
print("   - DataLakePrincipal: DataLakePrincipalIdentifier should be a string")
print("   - TableWildcard: Has empty props dictionary - should accept no parameters")
print("")

# Test a specific behavior
print("=== Testing TableWildcard behavior ===")
try:
    tw = TableWildcard()
    print(f"TableWildcard() created: {tw}")
    print(f"TableWildcard().to_dict(): {tw.to_dict()}")
except Exception as e:
    print(f"Error creating TableWildcard: {e}")

try:
    tw = TableWildcard(unexpected_param="value")
    print(f"TableWildcard with unexpected param created: {tw}")
except Exception as e:
    print(f"Error with unexpected param: {e}")

print("\n=== Testing required field validation ===")
try:
    # DataCellsFilter has required fields
    dcf = DataCellsFilter()  # Missing required fields
    print(f"DataCellsFilter created without required fields: {dcf}")
    dcf.to_dict()  # This should trigger validation
except Exception as e:
    print(f"Expected error: {e}")