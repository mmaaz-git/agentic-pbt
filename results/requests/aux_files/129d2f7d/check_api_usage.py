import requests.hooks

# Check if dispatch_hook is considered public API
print("Checking if dispatch_hook is public API...")
print("="*50)

# Public functions don't start with underscore
public_funcs = [name for name in dir(requests.hooks) if not name.startswith('_') and callable(getattr(requests.hooks, name))]
print(f"Public functions in requests.hooks: {public_funcs}")

# Check if it's exposed at package level
import requests
if hasattr(requests, 'dispatch_hook'):
    print("dispatch_hook is exposed at requests package level")
else:
    print("dispatch_hook is NOT exposed at requests package level")

# Check docstring
print("\n" + "="*50)
print("dispatch_hook docstring:")
print(requests.hooks.dispatch_hook.__doc__)

# Check if external code could import it
print("\n" + "="*50)
print("Testing direct import:")
try:
    from requests.hooks import dispatch_hook
    print("Can import: from requests.hooks import dispatch_hook")
    
    # Test what happens with direct usage
    print("\nDirect usage with non-dict hooks:")
    try:
        result = dispatch_hook("key", "not a dict", "data")
        print(f"Result: {result}")
    except AttributeError as e:
        print(f"Error: {e}")
except ImportError:
    print("Cannot import dispatch_hook directly")