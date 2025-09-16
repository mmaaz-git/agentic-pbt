"""
Test for potential Mermaid syntax injection through class names
"""

import sys
import types

sys.path.insert(0, '/root/hypothesis-llm/envs/sphinxcontrib-mermaid_env/lib/python3.13/site-packages')

from sphinxcontrib.mermaid.autoclassdiag import class_diagram

def test_class_name(name, description):
    """Test a specific class name for potential issues"""
    module = types.ModuleType("test_module")
    module.__name__ = "test_module"
    
    try:
        # Create class with potentially problematic name
        cls = type(name, (), {})
        cls.__module__ = "test_module"
        setattr(module, "TestClass", cls)  # Store with safe attribute name
        
        # Create a child
        child = type("Child", (cls,), {})
        child.__module__ = "test_module"
        module.Child = child
        
        sys.modules["test_module"] = module
        
        result = class_diagram("test_module", strict=False)
        
        print(f"\n{description}")
        print(f"Class name: '{name}'")
        print(f"Generated diagram:")
        for line in result.split('\n'):
            print(f"  {line}")
        
        # Check if the syntax looks valid
        if name and f"{name} <|-- Child" not in result:
            print("⚠️  WARNING: Expected inheritance not found in diagram!")
        if not name and " <|-- Child" in result:
            print("🐛 BUG: Empty parent name produces invalid Mermaid syntax!")
            
    except Exception as e:
        print(f"\n{description}")
        print(f"Class name: '{name}'")
        print(f"Error: {e}")
    finally:
        if "test_module" in sys.modules:
            del sys.modules["test_module"]


# Test various problematic names
test_class_name("", "Empty class name")
test_class_name("A <|-- B", "Injection attempt with inheritance syntax")
test_class_name("A\nB", "Newline in class name")
test_class_name("Class--", "Class name ending with dashes")
test_class_name("Class<>", "Class with angle brackets")
test_class_name("Class|Type", "Class with pipe character")
test_class_name("Class::Namespace", "Class with double colon")
test_class_name("Class`backtick`", "Class with backticks")
test_class_name("Class'quote'", "Class with quotes")
test_class_name('Class"doublequote"', "Class with double quotes")