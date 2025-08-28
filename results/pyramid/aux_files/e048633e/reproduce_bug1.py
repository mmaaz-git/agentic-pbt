#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from pyramid.predicates import RequestParamPredicate
from unittest.mock import Mock

# Test case that failed: key=' ' (space), value='' (empty string)
config = Mock()

# The parameter string is " =" (space equals empty)
param_str = " ="
print(f"Testing RequestParamPredicate with param_str: '{param_str}'")

pred = RequestParamPredicate(param_str, config)
print(f"Parsed reqs: {pred.reqs}")

context = {}
request = Mock()

# Test with the exact key-value pair
request.params = {' ': ''}  # space key with empty value
result = pred(context, request)
print(f"With params {{' ': ''}}: {result}")

# According to the parsing logic, ' =' should be parsed as:
# k=' ', v=''
# But after stripping: k='', v=''

# Test with empty key
request.params = {'': ''}
result2 = pred(context, request)
print(f"With params {{'': ''}}: {result2}")

# Let's inspect what the predicate actually expects
print(f"\nPredicate expects:")
for k, v in pred.reqs:
    print(f"  key='{k}', value='{v}'")

# The bug is that after stripping whitespace, the key becomes empty string
# But the request.params still has the original ' ' (space) key
# So the predicate can't find the stripped key '' in params with key ' '