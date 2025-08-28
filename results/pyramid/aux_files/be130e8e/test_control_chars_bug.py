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

# Test various control characters
control_chars = ['\n', '\r', '\r\n', '\t\n', 'param=value\n']

factory = AppendSlashNotFoundViewFactory()

for char in control_chars:
    request = MockRequest('/test', char)
    context = MockContext()
    
    try:
        result = factory(context, request)
        print(f"Query '{repr(char)}': OK - {type(result).__name__}")
    except ValueError as e:
        print(f"Query '{repr(char)}': FAILED - {e}")