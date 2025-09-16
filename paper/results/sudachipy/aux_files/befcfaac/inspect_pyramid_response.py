import inspect
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')
import pyramid.response

# Get all members
members = inspect.getmembers(pyramid.response)
print("=== Module Members ===")
for name, obj in members:
    if not name.startswith('_'):
        print(f"{name}: {type(obj).__name__}")

print("\n=== FileResponse Class ===")
print("Signature:", inspect.signature(pyramid.response.FileResponse.__init__))
print("\nDocstring:", pyramid.response.FileResponse.__doc__)

print("\n=== FileIter Class ===")
print("Signature:", inspect.signature(pyramid.response.FileIter.__init__))
print("\nDocstring:", pyramid.response.FileIter.__doc__)

print("\n=== Response Class ===")
# Check base class
print("Base classes:", [base.__name__ for base in pyramid.response.Response.__mro__[1:]])
print("Implements:", pyramid.response.Response.__implemented__)

print("\n=== _guess_type function ===")
print("Signature:", inspect.signature(pyramid.response._guess_type))