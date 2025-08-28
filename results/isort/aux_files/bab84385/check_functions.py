import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

import isort.utils
import inspect

# Check for exists_case_sensitive
if hasattr(isort.utils, 'exists_case_sensitive'):
    func = isort.utils.exists_case_sensitive
    print(f"exists_case_sensitive found!")
    print(f"  Signature: {inspect.signature(func)}")
    print(f"  Doc: {func.__doc__}")
    print(f"  Module: {func.__module__}")
    
    # Try to get source
    try:
        source = inspect.getsource(func)
        print(f"\nSource code:\n{source}")
    except:
        pass