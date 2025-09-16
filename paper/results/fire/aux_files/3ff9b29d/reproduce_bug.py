"""Minimal reproduction of the SetParseFns bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

from fire import decorators

def test_func():
    return 42

# Test with empty list
positional_fns = []
decorated = decorators.SetParseFns(*positional_fns)(test_func)
retrieved = decorators.GetParseFns(decorated)

print(f"Input positional_fns: {positional_fns}")
print(f"Input type: {type(positional_fns)}")
print(f"Retrieved positional: {retrieved['positional']}")
print(f"Retrieved type: {type(retrieved['positional'])}")
print(f"Are they equal? {retrieved['positional'] == positional_fns}")
print()

# Test with non-empty list
positional_fns = [int, float]
decorated2 = decorators.SetParseFns(*positional_fns)(test_func)
retrieved2 = decorators.GetParseFns(decorated2)

print(f"Input positional_fns: {positional_fns}")
print(f"Input type: {type(positional_fns)}")
print(f"Retrieved positional: {retrieved2['positional']}")
print(f"Retrieved type: {type(retrieved2['positional'])}")
print(f"Are they equal? {retrieved2['positional'] == positional_fns}")