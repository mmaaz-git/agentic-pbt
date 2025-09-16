"""Minimal reproduction of the serialization round-trip bug in dparse"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/dparse_env/lib/python3.13/site-packages')

import dparse.filetypes as filetypes
from dparse.dependencies import DependencyFile

# Create a simple DependencyFile
content = ""
file_type = filetypes.requirements_txt

# Create the DependencyFile
df = DependencyFile(content=content, file_type=file_type)

# Serialize it
serialized = df.serialize()
print("Serialized data keys:", serialized.keys())
print("Serialized data:", serialized)

# Try to deserialize - this should fail
try:
    deserialized = DependencyFile.deserialize(serialized)
    print("Deserialization succeeded unexpectedly!")
except TypeError as e:
    print(f"\n✗ Bug found: {e}")
    print("\nThe serialize() method includes 'resolved_dependencies' key,")
    print("but deserialize() passes all keys to __init__() which doesn't accept it.")
    
    # Show that resolved_dependencies is in serialized data
    print(f"\n'resolved_dependencies' in serialized data: {'resolved_dependencies' in serialized}")
    
    # Show DependencyFile.__init__ signature
    import inspect
    sig = inspect.signature(DependencyFile.__init__)
    print(f"\nDependencyFile.__init__ parameters: {list(sig.parameters.keys())}")
    print(f"'resolved_dependencies' is a parameter: {'resolved_dependencies' in sig.parameters}")