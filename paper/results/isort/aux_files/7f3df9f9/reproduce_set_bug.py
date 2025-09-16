import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

import ast
from isort.literal import assignment
from isort.settings import Config

# Test empty set formatting
code = "x = set()"
config = Config()

result = assignment(code, "set", ".py", config)
print(f"Input:  {code}")
print(f"Output: {result}")

# Extract the literal
_, literal_part = result.split(" = ", 1)
parsed = ast.literal_eval(literal_part.strip())

print(f"Parsed type: {type(parsed)}")
print(f"Is set? {isinstance(parsed, set)}")
print(f"Is dict? {isinstance(parsed, dict)}")

# This demonstrates the bug: empty sets become dicts when parsed
assert isinstance(parsed, set), f"Expected set, got {type(parsed)}"