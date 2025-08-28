#!/usr/bin/env python3
import troposphere.refactorspaces as refactorspaces
import inspect
import sys

# Let's understand the properties and methods better
classes = [
    refactorspaces.Application,
    refactorspaces.Environment,
    refactorspaces.Service,
    refactorspaces.Route,
    refactorspaces.ApiGatewayProxyInput,
    refactorspaces.DefaultRouteInput,
    refactorspaces.LambdaEndpointInput,
    refactorspaces.UriPathRouteInput,
    refactorspaces.UrlEndpointInput,
]

for cls in classes:
    print(f"\n=== {cls.__name__} ===")
    
    # Check props
    if hasattr(cls, 'props'):
        print(f"Props: {cls.props}")
    
    # Check resource_type  
    if hasattr(cls, 'resource_type'):
        print(f"Resource type: {cls.resource_type}")
    
    # Check required
    if hasattr(cls, 'required'):
        print(f"Required: {cls.required}")
        
    # Try to understand validation
    instance = None
    try:
        instance = cls("Test")
        print(f"Can create with just title: Yes")
    except Exception as e:
        print(f"Can create with just title: No - {e}")
    
    # If we can create an instance, test methods
    if instance:
        try:
            # Test to_dict
            d = instance.to_dict()
            print(f"to_dict() works: {type(d)} with keys {list(d.keys())[:5]}")
        except Exception as e:
            print(f"to_dict() error: {e}")
            
        try:
            # Test from_dict
            test_dict = {"Type": "Test"}
            new_instance = cls.from_dict("Test2", test_dict)
            print(f"from_dict() works: {type(new_instance)}")
        except Exception as e:
            print(f"from_dict() error: {e}")

# Test the boolean function
print("\n=== boolean function ===")
test_values = [True, False, 1, 0, "true", "false", "True", "False", None, "", "yes", []]
for val in test_values:
    try:
        result = refactorspaces.boolean(val)
        print(f"boolean({repr(val)}) = {result}")
    except Exception as e:
        print(f"boolean({repr(val)}) raised: {e}")