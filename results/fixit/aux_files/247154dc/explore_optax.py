#!/root/hypothesis-llm/envs/optax_env/bin/python

import sys
import inspect
import optax

# Check if optax_test exists
if hasattr(optax, 'optax_test'):
    target = optax.optax_test
    print(f"optax.optax_test found: {type(target)}")
    if inspect.ismodule(target):
        print(f"It's a module at: {target.__file__}")
    elif inspect.isfunction(target):
        print(f"It's a function with signature: {inspect.signature(target)}")
    elif inspect.isclass(target):
        print(f"It's a class")
else:
    # Try to import optax_test as a submodule
    try:
        from optax import optax_test
        print(f"optax.optax_test imported as module at: {optax_test.__file__}")
    except ImportError:
        # Check if it's optax.test or some other attribute
        print("optax.optax_test not found. Available attributes in optax:")
        attrs = [attr for attr in dir(optax) if not attr.startswith('_')]
        for attr in attrs[:20]:  # Show first 20 attributes
            print(f"  - {attr}: {type(getattr(optax, attr))}")