"""
Minimal reproduction of the bug in flask.ctx._AppCtxGlobals
"""

from flask.ctx import _AppCtxGlobals


def test_iteration_modification_bug():
    """Demonstrate that modifying _AppCtxGlobals during iteration raises RuntimeError"""
    g = _AppCtxGlobals()
    
    # Set up some attributes
    g.attr1 = "value1"
    g.attr2 = "value2"
    g.attr3 = "value3"
    
    # Try to modify during iteration
    collected = []
    try:
        for name in g:
            collected.append(name)
            if len(collected) == 1:
                # This will raise RuntimeError: dictionary changed size during iteration
                g.pop('attr3')
        print(f"Collected: {collected}")
    except RuntimeError as e:
        print(f"Error: {e}")
        print(f"Collected before error: {collected}")
        return False
    
    return True


if __name__ == "__main__":
    success = test_iteration_modification_bug()
    if not success:
        print("\nBug confirmed: Cannot modify _AppCtxGlobals during iteration")
        print("This violates the principle that iteration should be safe even with modifications")
        
        # Show the issue more clearly
        print("\nCode that fails:")
        print("""
g = _AppCtxGlobals()
g.attr1 = "value1"
g.attr2 = "value2"

for name in g:
    if name == 'attr1':
        g.pop('attr2')  # RuntimeError: dictionary changed size during iteration
""")
        
        # Compare with regular dict behavior
        print("\nNote: Python dicts have the same limitation:")
        d = {'attr1': 'value1', 'attr2': 'value2', 'attr3': 'value3'}
        try:
            for key in d:
                if key == 'attr1':
                    d.pop('attr3')
        except RuntimeError as e:
            print(f"Dict also fails: {e}")