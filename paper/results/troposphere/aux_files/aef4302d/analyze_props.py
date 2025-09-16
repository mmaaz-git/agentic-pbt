#!/usr/bin/env python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

import inspect
import troposphere.kendra as kendra
from troposphere import AWSProperty, AWSObject

# Analyze property patterns
def analyze_class(cls):
    """Analyze a single class for its properties"""
    results = {
        'name': cls.__name__,
        'type': 'AWSProperty' if issubclass(cls, AWSProperty) else 'AWSObject',
        'props': {}
    }
    
    if hasattr(cls, 'props'):
        for prop_name, prop_def in cls.props.items():
            prop_type, required = prop_def
            results['props'][prop_name] = {
                'type': str(prop_type),
                'required': required
            }
    
    return results

# Get all classes
aws_classes = []
for name, obj in inspect.getmembers(kendra):
    if inspect.isclass(obj) and (issubclass(obj, (AWSProperty, AWSObject))):
        aws_classes.append(obj)

print(f"Total classes: {len(aws_classes)}")
print("\n=== Property Patterns ===")

# Look for classes with integer properties
integer_props = []
boolean_props = []
list_props = []
string_props = []

for cls in aws_classes:
    if hasattr(cls, 'props'):
        for prop_name, prop_def in cls.props.items():
            prop_type, required = prop_def
            
            # Check for integer validator
            if str(prop_type) == "<function integer at":
                integer_props.append((cls.__name__, prop_name, required))
            # Check for boolean validator  
            elif str(prop_type) == "<function boolean at":
                boolean_props.append((cls.__name__, prop_name, required))
            # Check for list types
            elif str(prop_type).startswith("[<class"):
                list_props.append((cls.__name__, prop_name, required))
            # Check for string types
            elif prop_type == str:
                string_props.append((cls.__name__, prop_name, required))

print(f"\nInteger properties: {len(integer_props)}")
for cls_name, prop_name, required in integer_props[:5]:
    print(f"  - {cls_name}.{prop_name} (required={required})")

print(f"\nBoolean properties: {len(boolean_props)}")
for cls_name, prop_name, required in boolean_props[:5]:
    print(f"  - {cls_name}.{prop_name} (required={required})")

print(f"\nList properties: {len(list_props)}")
for cls_name, prop_name, required in list_props[:5]:
    print(f"  - {cls_name}.{prop_name} (required={required})")

print(f"\nString properties: {len(string_props)}")
for cls_name, prop_name, required in string_props[:5]:
    print(f"  - {cls_name}.{prop_name} (required={required})")

# Look at the validators module
print("\n=== Validator Functions ===")
import troposphere.validators as validators
validator_funcs = [name for name in dir(validators) if not name.startswith('_')]
print(f"Available validators: {validator_funcs[:10]}")