#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import troposphere
import troposphere.ce as ce
import inspect

print("troposphere.validators module:", hasattr(troposphere, 'validators'))
if hasattr(troposphere, 'validators'):
    print("validators.double:", hasattr(troposphere.validators, 'double'))
    if hasattr(troposphere.validators, 'double'):
        print("double function signature:", inspect.signature(troposphere.validators.double))
        print("double function source:")
        try:
            print(inspect.getsource(troposphere.validators.double))
        except:
            print("Could not get source")

print("\n=== Classes in troposphere.ce ===")
for name, obj in inspect.getmembers(ce):
    if inspect.isclass(obj) and not name.startswith('_'):
        print(f"\nClass: {name}")
        print(f"  Base classes: {[base.__name__ for base in obj.__bases__]}")
        if hasattr(obj, 'props'):
            print(f"  Properties: {obj.props}")
        if hasattr(obj, '__init__'):
            print(f"  __init__ signature: {inspect.signature(obj.__init__)}")

# Let's instantiate and test some objects
print("\n=== Testing instantiation ===")
try:
    tag = ce.ResourceTag(Key="TestKey", Value="TestValue")
    print(f"ResourceTag created: {tag.to_dict()}")
except Exception as e:
    print(f"Error creating ResourceTag: {e}")

try:
    subscriber = ce.Subscriber(Address="test@example.com", Type="EMAIL")
    print(f"Subscriber created: {subscriber.to_dict()}")
except Exception as e:
    print(f"Error creating Subscriber: {e}")