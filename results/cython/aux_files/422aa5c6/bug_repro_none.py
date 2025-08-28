import Cython.Tempita

# BUG: None should raise NameError but returns empty string
template = Cython.Tempita.Template('{{None}}')
result = template.substitute()
print(f"Result: {repr(result)}")  # Returns '' instead of raising NameError

# Compare with undefined variable which correctly raises NameError
try:
    template2 = Cython.Tempita.Template('{{undefined_var}}')
    result2 = template2.substitute()
except NameError as e:
    print(f"Undefined variable correctly raises: {e}")

# Also True and False behave similarly
template3 = Cython.Tempita.Template('{{True}} {{False}}')
result3 = template3.substitute()
print(f"True/False result: {repr(result3)}")  # Returns '1 0' instead of raising NameError