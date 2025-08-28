import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')
import inspect
import troposphere

# Check AWSObject and AWSProperty
print("=== AWSObject Methods ===")
for name, method in inspect.getmembers(troposphere.AWSObject):
    if not name.startswith('_') and callable(method):
        try:
            sig = inspect.signature(method)
            print(f"{name}: {sig}")
        except:
            print(f"{name}: (signature not available)")

print("\n=== AWSProperty Methods ===")
for name, method in inspect.getmembers(troposphere.AWSProperty):
    if not name.startswith('_') and callable(method):
        try:
            sig = inspect.signature(method)
            print(f"{name}: {sig}")
        except:
            print(f"{name}: (signature not available)")

# Check the boolean validator
print("\n=== boolean validator ===")
print(f"Signature: {inspect.signature(troposphere.validators.boolean)}")
print(f"Source:\n{inspect.getsource(troposphere.validators.boolean)}")