import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import inspect
from troposphere import frauddetector

# Get all classes
classes = [cls for name, cls in inspect.getmembers(frauddetector, inspect.isclass) 
           if cls.__module__ == 'troposphere.frauddetector']

for cls in classes:
    print(f"\n{cls.__name__}:")
    print(f"  Base classes: {[b.__name__ for b in cls.__bases__]}")
    if hasattr(cls, 'props'):
        print(f"  Properties: {list(cls.props.keys())}")
    if hasattr(cls, 'resource_type'):
        print(f"  Resource type: {cls.resource_type}")