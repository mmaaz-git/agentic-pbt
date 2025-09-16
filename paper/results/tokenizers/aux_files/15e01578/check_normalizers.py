import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/tokenizers_env/lib/python3.13/site-packages')

import tokenizers.normalizers as normalizers

# Check if there's a Strip normalizer
print("Checking tokenizers.normalizers for Strip:")
if hasattr(normalizers, 'Strip'):
    print("Found Strip in normalizers!")
    strip_norm = normalizers.Strip(left=1, right=1)
    print(f"Type: {type(strip_norm)}")
    print(f"Doc: {strip_norm.__doc__ if hasattr(strip_norm, '__doc__') else 'No doc'}")
else:
    print("No Strip in normalizers")

# List all normalizers
print("\nAll normalizers:")
import inspect
members = inspect.getmembers(normalizers)
for name, obj in members:
    if not name.startswith('_') and isinstance(obj, type):
        print(f"  - {name}")