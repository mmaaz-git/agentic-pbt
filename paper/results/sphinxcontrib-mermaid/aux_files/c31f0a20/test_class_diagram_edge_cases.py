import sys
import types
from hypothesis import given, strategies as st, settings, example
import pytest

sys.path.insert(0, '/root/hypothesis-llm/envs/sphinxcontrib-mermaid_env/lib/python3.13/site-packages')

from sphinxcontrib.mermaid.autoclassdiag import get_classes, class_diagram
from sphinxcontrib.mermaid.exceptions import MermaidError


# Test with classes that have __bases__ attribute but weird values
def test_class_with_modified_bases():
    """
    Test that class_diagram handles classes with modified __bases__.
    """
    module = types.ModuleType("test_module")
    module.__name__ = "test_module"
    
    # Create a normal class
    NormalClass = type("NormalClass", (), {})
    NormalClass.__module__ = "test_module"
    module.NormalClass = NormalClass
    
    # Create a class with empty name
    EmptyName = type("", (), {})
    EmptyName.__module__ = "test_module"
    module.EmptyName = EmptyName
    
    # Create child of empty-named class
    Child = type("Child", (EmptyName,), {})
    Child.__module__ = "test_module"
    module.Child = Child
    
    sys.modules["test_module"] = module
    
    try:
        result = class_diagram("test_module", strict=False)
        # Should handle empty class name
        print(f"Result with empty class name: {result}")
        assert "classDiagram" in result
        # The empty-named class should appear in the diagram
        assert " <|-- Child" in result
    finally:
        del sys.modules["test_module"]


# Test with class names containing special Mermaid syntax characters
@given(st.sampled_from([
    "Class<T>",  # Generic syntax
    "Class|Union",  # Pipe character
    "Class--Dashed",  # Dashes
    "Class<<Interface>>",  # Double angle brackets
    "Class::Namespace",  # Double colon
    "Class..Abstract",  # Dots
    "Class~Generic~",  # Tilde
    "Class#Private",  # Hash
    "Class+Public",  # Plus
    "Class-Private",  # Minus/hyphen
    "Class*Pointer",  # Asterisk
    "Class(Param)",  # Parentheses
    "Class[Array]",  # Brackets
    "Class{Dict}",  # Braces
]))
def test_class_names_with_mermaid_special_chars(special_name):
    """
    Test that class names with Mermaid special characters are handled.
    These characters might break the Mermaid diagram syntax.
    """
    module = types.ModuleType("test_module")
    module.__name__ = "test_module"
    
    # Create class with special name
    try:
        # Some names might not be valid Python identifiers
        cls = type(special_name, (), {})
        cls.__module__ = "test_module"
        setattr(module, special_name, cls)
        
        # Create a normal child
        child = type("Child", (cls,), {})
        child.__module__ = "test_module"
        module.Child = child
        
        sys.modules["test_module"] = module
        
        result = class_diagram("test_module", strict=False)
        
        # The diagram should contain the relationship
        # But the special characters might cause issues in Mermaid rendering
        assert "classDiagram" in result
        assert f"{special_name} <|-- Child" in result
        
        # Check if special characters are properly handled
        # Mermaid might require escaping for certain characters
        print(f"Special name '{special_name}' produced: {result}")
        
    except (ValueError, TypeError) as e:
        # Some names might not be valid Python class names
        print(f"Cannot create class with name '{special_name}': {e}")
    finally:
        if "test_module" in sys.modules:
            del sys.modules["test_module"]


# Test with unicode class names
@given(st.text(alphabet='αβγδεζηθικλμνξοπρστυφχψωΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ', min_size=1, max_size=10))
def test_unicode_class_names(unicode_name):
    """
    Test that class_diagram handles unicode class names.
    """
    if not unicode_name or not unicode_name[0].isidentifier():
        return  # Skip invalid identifiers
    
    module = types.ModuleType("test_module")
    module.__name__ = "test_module"
    
    try:
        # Create class with unicode name
        cls = type(unicode_name, (), {})
        cls.__module__ = "test_module"
        setattr(module, unicode_name, cls)
        
        # Create ASCII child
        child = type("Child", (cls,), {})
        child.__module__ = "test_module"
        module.Child = child
        
        sys.modules["test_module"] = module
        
        result = class_diagram("test_module", strict=False)
        
        # Should handle unicode names
        assert "classDiagram" in result
        assert f"{unicode_name} <|-- Child" in result
        
    except (ValueError, TypeError, UnicodeError) as e:
        print(f"Error with unicode name '{unicode_name}': {e}")
    finally:
        if "test_module" in sys.modules:
            del sys.modules["test_module"]


# Test with whitespace in class names (using setattr tricks)
def test_class_name_with_whitespace():
    """
    Test class_diagram with class names containing whitespace.
    This is possible through setattr even if not normal Python syntax.
    """
    module = types.ModuleType("test_module")
    module.__name__ = "test_module"
    
    # Create class with space in name via setattr
    cls_with_space = type("Class With Spaces", (), {})
    cls_with_space.__module__ = "test_module"
    setattr(module, "Class With Spaces", cls_with_space)
    
    # Create a normal child
    child = type("Child", (cls_with_space,), {})
    child.__module__ = "test_module"
    module.Child = child
    
    sys.modules["test_module"] = module
    
    try:
        result = class_diagram("test_module", strict=False)
        
        # Should handle names with spaces
        print(f"Result with spaces in name: {result}")
        assert "classDiagram" in result
        # The class with spaces should appear
        assert "Class With Spaces <|-- Child" in result
        
    finally:
        del sys.modules["test_module"]


# Test with classes having __name__ that differs from attribute name
def test_class_name_mismatch():
    """
    Test when a class's __name__ differs from its module attribute name.
    """
    module = types.ModuleType("test_module")
    module.__name__ = "test_module"
    
    # Create class with one name
    cls = type("ActualName", (), {})
    cls.__module__ = "test_module"
    # But store it with different name
    module.DifferentName = cls
    
    # Create child using the actual class
    child = type("Child", (cls,), {})
    child.__module__ = "test_module"
    module.Child = child
    
    sys.modules["test_module"] = module
    
    try:
        result = class_diagram("test_module", strict=False)
        
        # Uses __name__ attribute, not the module attribute name
        print(f"Result with name mismatch: {result}")
        assert "classDiagram" in result
        assert "ActualName <|-- Child" in result
        assert "DifferentName" not in result
        
    finally:
        del sys.modules["test_module"]


# Test with recursive full traversal
def test_deep_inheritance_chain():
    """
    Test class_diagram with very deep inheritance chain and full=True.
    """
    module = types.ModuleType("test_module")
    module.__name__ = "test_module"
    
    # Create a deep inheritance chain
    prev_cls = None
    depth = 50  # Deep chain
    
    for i in range(depth):
        name = f"Class{i}"
        if prev_cls:
            cls = type(name, (prev_cls,), {})
        else:
            cls = type(name, (), {})
        cls.__module__ = "test_module"
        setattr(module, name, cls)
        prev_cls = cls
    
    sys.modules["test_module"] = module
    
    try:
        # Test with full=True on the deepest class
        result = class_diagram(f"test_module.Class{depth-1}", full=True)
        
        # Should contain all inheritance relationships
        lines = result.strip().split('\n')
        assert lines[0] == "classDiagram"
        
        # Should have depth-1 inheritance relationships
        inheritance_lines = [line for line in lines[1:] if " <|-- " in line]
        assert len(inheritance_lines) == depth - 1
        
        # Check first and last relationships
        assert "Class0 <|-- Class1" in result
        assert f"Class{depth-2} <|-- Class{depth-1}" in result
        
    finally:
        del sys.modules["test_module"]


if __name__ == "__main__":
    # Run the tests
    test_class_with_modified_bases()
    test_class_names_with_mermaid_special_chars.hypothesis.fuzz_one_input(b"Class<T>")
    test_class_name_with_whitespace()
    test_class_name_mismatch()
    test_deep_inheritance_chain()
    print("All manual tests completed!")