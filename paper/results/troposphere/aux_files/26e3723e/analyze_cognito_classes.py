#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import inspect
import troposphere.cognito as cognito

# Get all AWS Object classes (not properties)
aws_objects = []
aws_properties = []

for name, obj in inspect.getmembers(cognito, inspect.isclass):
    if not name.startswith('_'):
        # Check if it's a resource (AWSObject) or property (AWSProperty)
        if hasattr(obj, 'resource_type'):
            aws_objects.append((name, obj))
        elif hasattr(obj, 'props'):
            aws_properties.append((name, obj))

print(f"AWS Resource Objects (have resource_type): {len(aws_objects)}")
for name, obj in aws_objects:
    print(f"  {name}: {obj.resource_type}")
    # Show required properties
    if hasattr(obj, 'props'):
        required = [k for k, v in obj.props.items() if isinstance(v, tuple) and len(v) > 1 and v[1]]
        print(f"    Required props: {required}")

print(f"\nAWS Properties (no resource_type): {len(aws_properties)}")
# Show a few examples
for name, obj in aws_properties[:10]:
    print(f"  {name}")
    if hasattr(obj, 'props'):
        required = [k for k, v in obj.props.items() if isinstance(v, tuple) and len(v) > 1 and v[1]]
        if required:
            print(f"    Required props: {required}")

# Check for validator functions
print("\nValidator functions:")
validators = [name for name in dir(cognito) if 'validate' in name.lower()]
for v in validators:
    print(f"  {v}")
    obj = getattr(cognito, v)
    if callable(obj):
        try:
            sig = inspect.signature(obj)
            print(f"    Signature: {sig}")
        except:
            pass