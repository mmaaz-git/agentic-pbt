import troposphere
import inspect

# Find helper functions used in validators
helpers = ['integer_range', 'positive_integer', 'integer', 'network_port']

for helper_name in helpers:
    if hasattr(troposphere, helper_name):
        func = getattr(troposphere, helper_name)
        print(f"\n{'='*60}")
        print(f"Helper: {helper_name}")
        print(f"Signature: {inspect.signature(func)}")
        try:
            source = inspect.getsource(func)
            print(source)
        except:
            print("Could not get source")
    else:
        print(f"\n{helper_name} not found in troposphere module")
        
# Check if they're in troposphere.validators
print("\n" + "="*60)
print("Checking troposphere.validators module:")
try:
    import troposphere.validators as validators_module
    for helper_name in helpers:
        if hasattr(validators_module, helper_name):
            func = getattr(validators_module, helper_name)
            print(f"\n{helper_name}:")
            print(f"  Signature: {inspect.signature(func)}")
            try:
                source = inspect.getsource(func)
                print("  Source:")
                for line in source.split('\n')[:20]:
                    print(f"    {line}")
            except:
                pass
except Exception as e:
    print(f"Error: {e}")