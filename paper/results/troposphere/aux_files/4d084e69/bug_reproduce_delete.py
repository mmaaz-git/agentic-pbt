import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.bcmdataexports as bcm

# Bug reproduction: Cannot delete optional properties after setting them
data_query = bcm.DataQuery(QueryStatement="SELECT * FROM table")

# Set an optional property
data_query.TableConfigurations = {"key": {"nested": "value"}}
print(f"Property set: {data_query.TableConfigurations}")

# Try to access it via dict
dict_repr = data_query.to_dict()
print(f"In dict: {dict_repr.get('TableConfigurations')}")

# Try to delete it
try:
    del data_query.TableConfigurations
    print("SUCCESS: Deleted optional property")
except AttributeError as e:
    print(f"BUG: Cannot delete property: {e}")
    
# Check if it's actually stored in __dict__ or properties
print(f"In __dict__: {'TableConfigurations' in data_query.__dict__}")
print(f"In properties: {'TableConfigurations' in data_query.properties}")

# Try to check via hasattr
print(f"hasattr returns: {hasattr(data_query, 'TableConfigurations')}")