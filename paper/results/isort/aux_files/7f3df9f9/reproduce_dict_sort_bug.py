import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

import ast
from isort.literal import assignment
from isort.settings import Config

# Test dict sorting - should be by values according to line 89 of literal.py
test_dict = {'a': 3, 'b': 1, 'c': 2}
code = f"x = {repr(test_dict)}"
config = Config()

result = assignment(code, "dict", ".py", config)
print(f"Input dict:  {test_dict}")
print(f"Output code: {result}")

# Extract the dict
_, literal_part = result.split(" = ", 1)
result_dict = ast.literal_eval(literal_part.strip())

# Check ordering
items = list(result_dict.items())
values = [v for k, v in items]

print(f"Result dict: {result_dict}")
print(f"Values order: {values}")
print(f"Expected order (sorted): {sorted(values)}")

# According to line 89, it should sort by values
assert values == sorted(values), f"Dict not sorted by values! Got {values}, expected {sorted(values)}"