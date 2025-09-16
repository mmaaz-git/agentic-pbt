import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/tokenizers_env/lib/python3.13/site-packages')

import inspect
import tokenizers.decoders as decoders

# Get all members
members = inspect.getmembers(decoders)
print("=== tokenizers.decoders members ===")
for name, obj in members:
    if not name.startswith('_'):
        print(f"{name}: {type(obj).__name__}")
        if hasattr(obj, '__doc__') and obj.__doc__:
            print(f"  Doc: {obj.__doc__[:200]}")