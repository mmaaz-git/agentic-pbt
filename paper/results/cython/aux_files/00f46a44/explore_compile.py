import inspect
import Cython

# Check the compile function
if hasattr(Cython, 'compile'):
    print("Cython.compile signature:")
    print(inspect.signature(Cython.compile))
    print("\nDocstring:")
    print(Cython.compile.__doc__)
    
# Let's also check Cython.Build for cythonize
try:
    from Cython.Build import cythonize
    print("\n\ncythonize signature:")
    print(inspect.signature(cythonize))
    print("\nDocstring:")
    print(cythonize.__doc__)
except ImportError as e:
    print(f"Could not import cythonize: {e}")

# Check StringIOTree which looks interesting
try:
    import Cython.StringIOTree as StringIOTree
    print("\n\nStringIOTree members:")
    for name, obj in inspect.getmembers(StringIOTree):
        if not name.startswith('_') and (inspect.isfunction(obj) or inspect.isclass(obj)):
            print(f"  {name}: {type(obj).__name__}")
            if inspect.isclass(obj):
                # Get its methods
                for method_name, method in inspect.getmembers(obj):
                    if not method_name.startswith('_') and inspect.ismethod(method) or inspect.isfunction(method):
                        print(f"    → {method_name}")
except ImportError as e:
    print(f"Could not import StringIOTree: {e}")

# Check Utils module
try:
    import Cython.Utils as Utils
    print("\n\nCython.Utils functions:")
    for name, obj in inspect.getmembers(Utils):
        if not name.startswith('_') and inspect.isfunction(obj):
            print(f"  {name}")
            if hasattr(obj, '__doc__') and obj.__doc__:
                doc_lines = obj.__doc__.strip().split('\n')
                if doc_lines:
                    print(f"    → {doc_lines[0][:80]}")
except ImportError as e:
    print(f"Could not import Utils: {e}")