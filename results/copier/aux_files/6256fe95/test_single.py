import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/copier_env/lib/python3.13/site-packages')

import yaml
from copier._user_data import parse_yaml_list

# Test case that might reveal a bug
test_yaml = """
- - nested
  - list
- "string"
"""

try:
    result = parse_yaml_list(test_yaml)
    print(f"Result: {result}")
    print(f"Length: {len(result)}")
    
    # Try to parse the first item back
    first_item = result[0]
    print(f"First item raw: {first_item}")
    reparsed = yaml.safe_load(first_item)
    print(f"First item reparsed: {reparsed}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()