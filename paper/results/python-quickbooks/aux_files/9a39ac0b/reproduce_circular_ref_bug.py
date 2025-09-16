"""Minimal reproduction of circular reference bug in quickbooks.mixins.to_dict"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/python-quickbooks_env/lib/python3.13/site-packages')

from quickbooks.objects.base import QuickbooksBaseObject
from quickbooks.mixins import to_dict

# Create a simple object that can have circular references
class SimpleObject(QuickbooksBaseObject):
    def __init__(self):
        self.name = ""
        self.reference = None

# Create two objects
obj1 = SimpleObject()
obj1.name = "Object 1"

obj2 = SimpleObject()
obj2.name = "Object 2"

# Create circular reference
obj1.reference = obj2
obj2.reference = obj1

# This will cause RecursionError
try:
    result = to_dict(obj1)
    print("Success! Result:", result)
except RecursionError as e:
    print(f"BUG CONFIRMED: RecursionError occurred when converting object with circular reference to dict")
    print(f"Error: {e}")