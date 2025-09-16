import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from troposphere.appintegrations import ExternalUrlConfig

print("Testing different ways to handle optional fields:")

print("\n1. Not providing optional field at all:")
try:
    config = ExternalUrlConfig(
        AccessUrl="https://example.com"
        # ApprovedOrigins not provided
    )
    print(f"Success - Created without ApprovedOrigins")
    print(f"to_dict: {config.to_dict()}")
except Exception as e:
    print(f"Failed: {e}")

print("\n2. Providing None explicitly:")
try:
    config = ExternalUrlConfig(
        AccessUrl="https://example.com",
        ApprovedOrigins=None
    )
    print(f"Success - Created with ApprovedOrigins=None")
    print(f"to_dict: {config.to_dict()}")
except Exception as e:
    print(f"Failed: {e}")

print("\n3. Providing empty list:")
try:
    config = ExternalUrlConfig(
        AccessUrl="https://example.com",
        ApprovedOrigins=[]
    )
    print(f"Success - Created with ApprovedOrigins=[]")
    print(f"to_dict: {config.to_dict()}")
except Exception as e:
    print(f"Failed: {e}")

print("\n4. Providing list with values:")
try:
    config = ExternalUrlConfig(
        AccessUrl="https://example.com",
        ApprovedOrigins=["https://allowed.com"]
    )
    print(f"Success - Created with ApprovedOrigins=['https://allowed.com']")
    print(f"to_dict: {config.to_dict()}")
except Exception as e:
    print(f"Failed: {e}")

print("\n\nAnalysis:")
print("The library accepts:")
print("- Not providing the optional field at all ✓")
print("- Empty list ✓")
print("- List with values ✓")
print("But rejects:")
print("- Explicitly passing None ✗")
print("\nThis is inconsistent behavior - if a field is optional (False in props),")
print("the library should accept None as a valid value.")