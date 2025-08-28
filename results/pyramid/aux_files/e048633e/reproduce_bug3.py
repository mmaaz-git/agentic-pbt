#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from pyramid.predicates import MatchParamPredicate
from unittest.mock import Mock

config = Mock()

# Test case that failed: duplicate keys with different values
# params = [('0', ''), ('0', '0')]
param_strings = ['0=', '0=0']  # Same key '0' with values '' and '0'

print(f"Input param_strings: {param_strings}")

pred = MatchParamPredicate(param_strings, config)
print(f"Parsed reqs: {pred.reqs}")

context = {}
request = Mock()

# The test created a dict from params, which overwrites duplicates
# {k: v for k, v in [('0', ''), ('0', '0')]} becomes {'0': '0'}
request.matchdict = {'0': '0'}  # Only the last value is kept

result = pred(context, request)
print(f"With matchdict {{'0': '0'}}: {result}")

# Let's check what the predicate actually expects
print(f"\nPredicate expects ALL of these to match:")
for k, v in pred.reqs:
    print(f"  key='{k}', value='{v}'")

# The bug is that MatchParamPredicate expects ALL key-value pairs to match
# but with duplicate keys, only one can match in a dict
# This is actually my test that's wrong - I shouldn't test with duplicate keys
# because that's not a realistic use case

# However, let's check if the predicate handles this gracefully
request.matchdict = {'0': ''}  # Try with the first value
result2 = pred(context, request)
print(f"\nWith matchdict {{'0': ''}}: {result2}")

# The predicate correctly checks all requirements
# But duplicate keys in requirements don't make sense in practice