import sys
import os
import types
from hypothesis import given, strategies as st, assume, settings, example
import pytest

# Add the site-packages to path for imports
sys.path.insert(0, '/root/hypothesis-llm/envs/sphinxcontrib-mermaid_env/lib/python3.13/site-packages')

from sphinxcontrib.mermaid import align_spec, Mermaid
from sphinxcontrib.mermaid.autoclassdiag import get_classes, class_diagram
from sphinxcontrib.mermaid.exceptions import MermaidError
from docutils.parsers.rst import directives
from sphinx.errors import ExtensionError


# Test edge cases in class_diagram with cyclic inheritance
@given(st.booleans())
def test_class_diagram_cyclic_inheritance(full):
    """
    Test that class_diagram handles cyclic inheritance patterns.
    This tests robustness against unusual inheritance patterns.
    """
    module = types.ModuleType("test_module")
    module.__name__ = "test_module"
    
    # Create classes with complex inheritance
    A = type("A", (), {})
    A.__module__ = "test_module"
    module.A = A
    
    B = type("B", (A,), {})
    B.__module__ = "test_module"
    module.B = B
    
    # Create a class that inherits from both A and B (diamond inheritance)
    C = type("C", (A, B), {})
    C.__module__ = "test_module"
    module.C = C
    
    sys.modules["test_module"] = module
    
    try:
        # This should not crash despite complex inheritance
        result = class_diagram("test_module.C", full=full)
        
        # Should contain inheritance relationships
        assert "classDiagram" in result
        if full:
            # When full=True, should trace all bases
            assert "A <|-- B" in result
            assert "A <|-- C" in result
            assert "B <|-- C" in result
        else:
            # When full=False, only direct bases
            assert "A <|-- C" in result
            assert "B <|-- C" in result
    finally:
        del sys.modules["test_module"]


# Test with reserved/special class names
@given(st.sampled_from([
    "__init__",
    "__main__",
    "__doc__",
    "None",
    "True", 
    "False",
    "type",
    "object"
]))
def test_class_diagram_special_names(special_name):
    """
    Test that class_diagram handles special/reserved Python names.
    """
    module = types.ModuleType("test_module")
    module.__name__ = "test_module"
    
    # Skip 'object' as it's filtered out in the code
    if special_name == "object":
        return
    
    # Create class with special name
    cls = type(special_name, (), {})
    cls.__module__ = "test_module"
    setattr(module, special_name, cls)
    
    # Create a child class
    child = type("Child", (cls,), {})
    child.__module__ = "test_module"
    module.Child = child
    
    sys.modules["test_module"] = module
    
    try:
        result = class_diagram("test_module", strict=False)
        
        # Should handle special names correctly
        assert "classDiagram" in result
        assert f"{special_name} <|-- Child" in result
    finally:
        del sys.modules["test_module"]


# Test get_classes with namespace filtering
@given(st.sampled_from(["test", "test.sub", "other", None]))
def test_class_diagram_namespace_filtering(namespace):
    """
    Test that namespace parameter correctly filters inheritance.
    """
    module = types.ModuleType("test_module")
    module.__name__ = "test_module"
    
    # Create classes with different module attributes
    TestClass = type("TestClass", (), {})
    TestClass.__module__ = "test.main"
    module.TestClass = TestClass
    
    TestSubClass = type("TestSubClass", (), {})
    TestSubClass.__module__ = "test.sub.module"
    module.TestSubClass = TestSubClass
    
    OtherClass = type("OtherClass", (), {})
    OtherClass.__module__ = "other.module"
    module.OtherClass = OtherClass
    
    # Create inheritance
    Child = type("Child", (TestClass, TestSubClass, OtherClass), {})
    Child.__module__ = "test_module"
    module.Child = Child
    
    sys.modules["test_module"] = module
    
    try:
        result = class_diagram("test_module.Child", namespace=namespace)
        
        if namespace is None:
            # Should include all inheritances
            assert "TestClass <|-- Child" in result
            assert "TestSubClass <|-- Child" in result
            assert "OtherClass <|-- Child" in result
        elif namespace == "test":
            # Should include only test.* modules
            assert "TestClass <|-- Child" in result
            assert "TestSubClass <|-- Child" in result
            assert "OtherClass <|-- Child" not in result
        elif namespace == "test.sub":
            # Should include only test.sub.* modules
            assert "TestClass <|-- Child" not in result
            assert "TestSubClass <|-- Child" in result
            assert "OtherClass <|-- Child" not in result
        elif namespace == "other":
            # Should include only other.* modules
            assert "TestClass <|-- Child" not in result
            assert "TestSubClass <|-- Child" not in result
            assert "OtherClass <|-- Child" in result
    finally:
        del sys.modules["test_module"]


# Test with very long class names
@given(st.text(alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_', 
               min_size=100, max_size=200))
def test_class_diagram_long_names(long_name):
    """
    Test that class_diagram handles very long class names.
    """
    # Ensure name starts with letter
    if not long_name[0].isalpha():
        long_name = "A" + long_name
    
    module = types.ModuleType("test_module")
    module.__name__ = "test_module"
    
    # Create class with very long name
    cls = type(long_name, (), {})
    cls.__module__ = "test_module"
    setattr(module, long_name, cls)
    
    # Create child
    child = type("Child", (cls,), {})
    child.__module__ = "test_module"
    module.Child = child
    
    sys.modules["test_module"] = module
    
    try:
        result = class_diagram("test_module", strict=False)
        
        # Should handle long names without truncation
        assert f"{long_name} <|-- Child" in result
    finally:
        del sys.modules["test_module"]


# Test empty module name edge case
def test_get_classes_empty_module_name():
    """
    Test get_classes with empty or invalid module names.
    """
    # Empty module name should raise appropriate error
    with pytest.raises((MermaidError, ExtensionError)):
        list(get_classes(""))
    
    # Module that doesn't exist
    with pytest.raises((MermaidError, ExtensionError)):
        list(get_classes("nonexistent_module_xyz"))


# Test class with many bases
@given(st.integers(min_value=2, max_value=10))
def test_class_diagram_many_bases(num_bases):
    """
    Test class_diagram with classes having many base classes.
    """
    module = types.ModuleType("test_module")
    module.__name__ = "test_module"
    
    # Create multiple base classes
    bases = []
    for i in range(num_bases):
        base_name = f"Base{i}"
        base = type(base_name, (), {})
        base.__module__ = "test_module"
        setattr(module, base_name, base)
        bases.append(base)
    
    # Create child with all bases
    child = type("Child", tuple(bases), {})
    child.__module__ = "test_module"
    module.Child = child
    
    sys.modules["test_module"] = module
    
    try:
        result = class_diagram("test_module.Child", full=False)
        
        # Should have all inheritance relationships
        lines = result.strip().split('\n')
        assert lines[0] == "classDiagram"
        
        # Count inheritance lines (excluding the classDiagram header)
        inheritance_lines = [line for line in lines[1:] if " <|-- " in line]
        assert len(inheritance_lines) == num_bases
        
        # Check all bases are represented
        for i in range(num_bases):
            assert f"Base{i} <|-- Child" in result
    finally:
        del sys.modules["test_module"]


# Test align_spec with unicode and special characters
@given(st.text(alphabet='αβγδεζηθικλμνξοπρστυφχψω←→↑↓∀∃∅∈∉⊂⊃⊆⊇∪∩', min_size=1))
def test_align_spec_unicode(unicode_text):
    """
    Test that align_spec properly rejects unicode/special characters.
    """
    # These should all be invalid
    with pytest.raises(ValueError):
        align_spec(unicode_text)


# Test align_spec with case sensitivity
@given(st.sampled_from(["LEFT", "Center", "RIGHT", "Left", "CENTER", "Right"]))
def test_align_spec_case_sensitivity(mixed_case):
    """
    Test that align_spec is case-sensitive (should reject mixed case).
    """
    # align_spec uses directives.choice which is case-sensitive
    with pytest.raises(ValueError):
        align_spec(mixed_case)