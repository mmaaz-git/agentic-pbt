import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/lml_env/lib/python3.13/site-packages')

from lml.utils import PythonObjectEncoder
from json import JSONEncoder

# The bug: PythonObjectEncoder.default() incorrectly handles basic types
# When basic types are passed to default(), it tries to call parent's default()
# which always raises TypeError

encoder = PythonObjectEncoder()

# According to the code on line 24, these types should be handled specially
basic_types = [None, True, 42, 3.14, "hello", [1, 2], {"k": "v"}]

print("Testing direct call to default() method:")
print("According to lines 23-25, basic types should call JSONEncoder.default()")
print("But JSONEncoder.default() always raises TypeError!\n")

for obj in basic_types:
    try:
        # The code checks: if isinstance(obj, a_list_of_types):
        # where a_list_of_types = (list, dict, str, int, float, bool, type(None))
        
        # If true, it does: return JSONEncoder.default(self, obj)
        # But JSONEncoder.default() ALWAYS raises TypeError!
        
        result = encoder.default(obj)
        print(f"✓ {obj!r} -> {result}")
    except TypeError as e:
        print(f"✗ {obj!r} -> TypeError (Bug!)")

print("\n" + "="*60)
print("BUG ANALYSIS:")
print("="*60)
print("The logic in lines 23-25 is flawed:")
print("  if isinstance(obj, a_list_of_types):")
print("      return JSONEncoder.default(self, obj)  # <- This ALWAYS raises!")
print("\nThe parent JSONEncoder.default() is designed to always raise TypeError")
print("for ANY input, as seen in json/encoder.py line 180.")
print("\nCorrect behavior would be to just return the object for basic types,")
print("not delegate to parent's default().")