import inspect
import Cython.Shadow as Shadow

# Check if there's source code available for typeof
print("Checking typeof function details:")
print(f"typeof function: {Shadow.typeof}")
print(f"typeof docstring: {Shadow.typeof.__doc__}")

# Try to get source
try:
    source = inspect.getsource(Shadow.typeof)
    print("\ntypeof source code:")
    print(source)
except Exception as e:
    print(f"\nCould not get source: {e}")

# Check the module to see if there's any documentation about this
print("\nCython.Shadow module docstring:")
print(Shadow.__doc__)

# Let's also check what the function name suggests
print("\nAnalyzing function behavior:")
print("The function is named 'typeof', which in many languages returns type information.")
print("In TypeScript/JavaScript, 'typeof' returns strings like 'number', 'string', etc.")
print("In C/C++, 'typeof'/'decltype' returns actual types.")
print("Python's built-in is 'type()' which returns type objects.")
print("\nGiven Cython bridges Python and C, the string return might be intentional")