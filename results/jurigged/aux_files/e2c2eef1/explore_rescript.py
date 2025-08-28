import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/jurigged_env/lib/python3.13/site-packages')

import jurigged.rescript
import inspect

print("Module functions:")
print("-" * 40)
members = inspect.getmembers(jurigged.rescript, inspect.isfunction)
for name, func in members:
    if not name.startswith('_'):
        sig = inspect.signature(func)
        doc = inspect.getdoc(func)
        print(f"\n{name}{sig}")
        if doc:
            print(f"  Doc: {doc[:150]}...")