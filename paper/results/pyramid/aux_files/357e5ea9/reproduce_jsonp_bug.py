#!/usr/bin/env python3
"""Reproducer for JSONP callback validation being overly restrictive."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from pyramid.renderers import JSONP
from pyramid.httpexceptions import HTTPBadRequest

# Test the JSONP renderer with common short callback names
jsonp_renderer = JSONP()

class MockInfo:
    pass

class MockRequest:
    def __init__(self, callback):
        self.GET = {'callback': callback}
        self.response = MockResponse()

class MockResponse:
    def __init__(self):
        self.default_content_type = 'text/html'
        self.content_type = 'text/html'

render_func = jsonp_renderer(MockInfo())

# Test data
test_data = {"message": "Hello"}

# These are all valid JavaScript identifiers that are commonly used
# but will be rejected by Pyramid's JSONP validation
short_callbacks = ['cb', 'fn', 'f', '_', '$']

print("Testing common JSONP callback names:")
print("-" * 40)

for callback in short_callbacks:
    try:
        request = MockRequest(callback)
        system = {'request': request}
        result = render_func(test_data, system)
        print(f"✓ '{callback}' accepted")
    except HTTPBadRequest as e:
        print(f"✗ '{callback}' rejected - {e}")

print("\nThese 3+ character callbacks work:")
print("-" * 40)

working_callbacks = ['foo', 'bar', 'callback', '_fn', '$cb']
for callback in working_callbacks:
    try:
        request = MockRequest(callback)
        system = {'request': request}
        result = render_func(test_data, system)
        print(f"✓ '{callback}' accepted")
    except HTTPBadRequest as e:
        print(f"✗ '{callback}' rejected")