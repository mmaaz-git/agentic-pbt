"""
Reproduction script for empty class name bug in sphinxcontrib-mermaid
"""

import sys
import types

sys.path.insert(0, '/root/hypothesis-llm/envs/sphinxcontrib-mermaid_env/lib/python3.13/site-packages')

from sphinxcontrib.mermaid.autoclassdiag import class_diagram

# Create test module
module = types.ModuleType("test_module")
module.__name__ = "test_module"

# Create a class with empty name (this is technically possible in Python)
EmptyNameClass = type("", (), {})
EmptyNameClass.__module__ = "test_module"
module.EmptyNameClass = EmptyNameClass

# Create a child class that inherits from the empty-named class
ChildClass = type("ChildClass", (EmptyNameClass,), {})
ChildClass.__module__ = "test_module"
module.ChildClass = ChildClass

# Register the module
sys.modules["test_module"] = module

# Generate the class diagram
result = class_diagram("test_module", strict=False)

print("Generated Mermaid diagram:")
print(result)
print("\nProblem: The parent class name is empty, producing invalid Mermaid syntax:")
print("' <|-- ChildClass' instead of 'ParentName <|-- ChildClass'")

# This invalid syntax would fail when rendered by Mermaid
# Expected: Either handle empty names gracefully or raise an error
# Actual: Produces invalid Mermaid syntax

# Clean up
del sys.modules["test_module"]