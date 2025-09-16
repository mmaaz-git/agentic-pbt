"""Minimal reproduction of the IndexError bug in GetLastHealthyElement."""

import fire.trace

# Create a FireTrace
trace = fire.trace.FireTrace(initial_component=object(), name="test")

# Simulate an empty trace (this could happen in edge cases)
trace.elements = []

# This will raise IndexError
try:
    result = trace.GetLastHealthyElement()
    print(f"Result: {result}")
except IndexError as e:
    print(f"Bug confirmed: IndexError when calling GetLastHealthyElement on empty trace")
    print(f"Error: {e}")
    
    # Show the problematic code
    import inspect
    print("\nProblematic code in GetLastHealthyElement:")
    print(inspect.getsource(fire.trace.FireTrace.GetLastHealthyElement))