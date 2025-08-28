#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from pyramid.predicates import AcceptPredicate
from unittest.mock import Mock

config = Mock()

# Test with a list
accept_values = ['text/html']
pred = AcceptPredicate(accept_values, config)

print(f"Input: {accept_values}")
print(f"Type of input: {type(accept_values)}")
print(f"Stored values: {pred.values}")
print(f"Type of stored values: {type(pred.values)}")

# Check the source code behavior
# From the source: if not is_nonstr_iter(values): values = (values,)
# So it only converts to tuple if it's NOT an iterable
# Lists are iterables, so they're kept as-is

# This is not a bug - my test was wrong. AcceptPredicate stores
# lists as lists, not converting them to tuples