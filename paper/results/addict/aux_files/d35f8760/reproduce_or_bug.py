import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/addict_env/lib/python3.13/site-packages')

from addict import Dict

# Minimal reproduction of the bug
d1 = {'a': {'a': None}}
d2 = {'a': {}}

dict1 = Dict(d1)
dict2 = Dict(d2)

result = dict1 | dict2

print(f"d1: {d1}")
print(f"d2: {d2}")
print(f"dict1: {dict1.to_dict()}")
print(f"dict2: {dict2.to_dict()}")
print(f"result: {result.to_dict()}")
print(f"Expected result['a']: {d2['a']}")
print(f"Actual result['a']: {result['a'].to_dict()}")

# The bug: result['a'] should be {} but it's {'a': None}
assert result['a'].to_dict() == d2['a'], f"Expected {d2['a']}, got {result['a'].to_dict()}"