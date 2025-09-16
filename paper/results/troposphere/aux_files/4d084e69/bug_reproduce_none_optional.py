import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere.bcmdataexports as bcm

# Bug reproduction: Cannot set optional properties to None
data_query = bcm.DataQuery(QueryStatement="SELECT * FROM table")

# This should work for an optional property, but raises TypeError
try:
    data_query.TableConfigurations = None
    print("SUCCESS: Set optional property to None")
except TypeError as e:
    print(f"BUG: Cannot set optional property to None: {e}")

# Also test with empty dict (should work)
data_query.TableConfigurations = {}
print(f"Empty dict works: {data_query.TableConfigurations}")