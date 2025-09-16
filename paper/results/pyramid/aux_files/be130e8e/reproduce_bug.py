import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from pyramid.view import AppendSlashNotFoundViewFactory
from pyramid.httpexceptions import HTTPTemporaryRedirect
from pyramid.interfaces import IRoutesMapper

class MockRoute:
    def match(self, path):
        return {'match': 'data'} if path.endswith('/') else None

class MockMapper:
    def get_routes(self):
        return [MockRoute()]

class MockRegistry:
    def queryUtility(self, interface):
        if interface == IRoutesMapper:
            return MockMapper()
        return None

class MockRequest:
    def __init__(self, path, query_string):
        self.path_info = path
        self.path = path
        self.query_string = query_string
        self.registry = MockRegistry()

class MockContext:
    pass

# Test with a query string containing a newline character
factory = AppendSlashNotFoundViewFactory()
request = MockRequest('/test', '\n')
context = MockContext()

try:
    result = factory(context, request)
    print(f"Result type: {type(result)}")
    if isinstance(result, HTTPTemporaryRedirect):
        print(f"Redirect location: {result.location}")
except ValueError as e:
    print(f"ERROR: {e}")
    print("Bug confirmed: Query strings with control characters cause ValueError")