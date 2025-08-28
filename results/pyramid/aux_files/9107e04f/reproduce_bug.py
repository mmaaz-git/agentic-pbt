"""Minimal reproduction of the _add_vary bug in pyramid.static"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from pyramid.static import _add_vary
from unittest.mock import Mock

# Create a response mock with existing duplicate vary headers
response = Mock()
response.vary = ['Accept-Encoding', 'Accept-Encoding']

print("Initial vary headers:", response.vary)
print("Initial vary headers (unique):", set([h.lower() for h in response.vary]))

# Try to add 'Accept-Encoding' again
_add_vary(response, 'Accept-Encoding')

print("After _add_vary:", response.vary)
print("After _add_vary (unique):", set([h.lower() for h in response.vary]))

# The issue: _add_vary doesn't clean up existing duplicates
# It only prevents adding new duplicates
print("\nBug: _add_vary preserves existing duplicates in response.vary")
print("Expected: response.vary should not contain duplicates")
print("Actual: response.vary =", response.vary)