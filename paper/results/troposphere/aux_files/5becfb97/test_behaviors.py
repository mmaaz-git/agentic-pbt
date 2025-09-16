import sys
sys.path.insert(0, './venv/lib/python3.13/site-packages')

import troposphere.lakeformation as lf
from troposphere.lakeformation import *
from troposphere import AWSObject, AWSProperty
from troposphere.validators import boolean
import inspect

print("=== Testing AWSObject behaviors ===")

# Test DataCellsFilter with title
try:
    dcf = DataCellsFilter("MyFilter")
    print(f"DataCellsFilter created with title: {dcf}")
    print(f"DataCellsFilter title: {dcf.title}")
    # Now try to_dict without required fields
    try:
        result = dcf.to_dict()
        print(f"to_dict() succeeded without required fields: {result}")
    except Exception as e:
        print(f"to_dict() validation error (expected): {e}")
except Exception as e:
    print(f"Error creating DataCellsFilter: {e}")

print("\n=== Testing from_dict/to_dict round-trip ===")
try:
    # Create a valid DataCellsFilter
    dcf = DataCellsFilter(
        "MyFilter",
        DatabaseName="mydb",
        Name="myfilter",
        TableCatalogId="12345",
        TableName="mytable"
    )
    print(f"Created DataCellsFilter: {dcf}")
    
    # Convert to dict
    dict_repr = dcf.to_dict()
    print(f"to_dict result: {dict_repr}")
    
    # Try from_dict
    if hasattr(DataCellsFilter, 'from_dict'):
        reconstructed = DataCellsFilter.from_dict("MyFilter2", dict_repr)
        print(f"from_dict succeeded: {reconstructed}")
        print(f"Round-trip match: {reconstructed.to_dict() == dict_repr}")
except Exception as e:
    print(f"Error in round-trip test: {e}")

print("\n=== Testing boolean validator edge cases ===")
test_values = [
    True, False,
    1, 0,
    "1", "0",
    "true", "false",
    "True", "False",
    # Edge cases
    "TRUE", "FALSE",
    "tRuE", "fAlSe",
    2, -1,
    "", None,
    [], {},
    "yes", "no"
]

for val in test_values:
    try:
        result = boolean(val)
        print(f"boolean({repr(val)}) = {result}")
    except ValueError:
        print(f"boolean({repr(val)}) = ValueError")
    except Exception as e:
        print(f"boolean({repr(val)}) = {type(e).__name__}: {e}")

print("\n=== Testing list type validation ===")
try:
    # ColumnWildcard expects list of strings
    cw = ColumnWildcard(ExcludedColumnNames="not_a_list")
    print(f"ColumnWildcard with string instead of list: {cw}")
    cw.to_dict()
except Exception as e:
    print(f"Expected type error: {e}")

try:
    # ColumnWildcard with list of non-strings
    cw = ColumnWildcard(ExcludedColumnNames=[1, 2, 3])
    print(f"ColumnWildcard with list of ints: {cw}")
    dict_repr = cw.to_dict()
    print(f"to_dict result: {dict_repr}")
except Exception as e:
    print(f"Error with list of ints: {e}")