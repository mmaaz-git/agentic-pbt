#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sudachipy_env/lib/python3.13/site-packages')

from sudachipy import config

# Demonstrate the mutation bug
test_dict = {"keep": "value", "remove": None, "another": 42}
print(f"Before _filter_nulls: {test_dict}")

result = config._filter_nulls(test_dict)

print(f"After _filter_nulls: {test_dict}")
print(f"Input was mutated: {test_dict != {'keep': 'value', 'remove': None, 'another': 42}}")
print(f"Result is same object: {result is test_dict}")

assert "remove" not in test_dict, "Key with None value was deleted from input"
assert result is test_dict, "Function returns the mutated input object"