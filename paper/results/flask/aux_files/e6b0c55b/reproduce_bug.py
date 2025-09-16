"""Minimal reproduction of the context push/pop state sharing issue."""

import flask
from flask import g

app = flask.Flask(__name__)

print("Demonstrating unexpected behavior with multiple context pushes:\n")

with app.app_context() as ctx:
    # Set initial value
    g.data = "initial"
    print(f"1. Set g.data = 'initial'")
    
    # Push the same context again
    ctx.push()
    print(f"2. After ctx.push(), g.data = '{g.data}'")
    
    # Modify the value
    g.data = "modified"
    print(f"3. Modified g.data = 'modified'")
    
    # Push once more
    ctx.push()
    print(f"4. After another ctx.push(), g.data = '{g.data}'")
    
    # Pop back
    ctx.pop()
    print(f"5. After ctx.pop(), g.data = '{g.data}'")
    
    # Pop again
    ctx.pop()
    print(f"6. After another ctx.pop(), g.data = '{g.data}'")

print("\n" + "="*60)
print("ISSUE: The g object state is shared across all pushes of the")
print("same context, rather than each push creating a fresh g object.")
print("This could lead to unexpected state leakage in nested contexts.")
print("="*60)