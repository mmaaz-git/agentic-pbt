import inspect
import Cython.StringIOTree as StringIOTree

# Get the StringIOTree class
if hasattr(StringIOTree, 'StringIOTree'):
    cls = StringIOTree.StringIOTree
    print(f"StringIOTree class: {cls}")
    print(f"Class docstring: {cls.__doc__}")
    
    # Get the class methods
    print("\nClass methods:")
    for name in dir(cls):
        if not name.startswith('_'):
            attr = getattr(cls, name)
            if callable(attr):
                print(f"  {name}")
                try:
                    sig = inspect.signature(attr)
                    print(f"    Signature: {sig}")
                except (ValueError, TypeError):
                    pass
                if hasattr(attr, '__doc__') and attr.__doc__:
                    doc_lines = attr.__doc__.strip().split('\n')
                    if doc_lines:
                        print(f"    Docstring: {doc_lines[0][:100]}")

# Check what else is in the module
print("\n\nOther module members:")
for name, obj in inspect.getmembers(StringIOTree):
    if not name.startswith('_') and not name == 'StringIOTree':
        print(f"  {name}: {type(obj).__name__}")