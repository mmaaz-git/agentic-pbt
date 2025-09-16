import sys
import os
import hashlib
import inspect
import types
from hypothesis import given, strategies as st, assume, settings
from hypothesis.strategies import text, lists, sampled_from, composite
import pytest

# Add the site-packages to path for imports
sys.path.insert(0, '/root/hypothesis-llm/envs/sphinxcontrib-mermaid_env/lib/python3.13/site-packages')

from sphinxcontrib.mermaid import align_spec, figure_wrapper
from sphinxcontrib.mermaid.autoclassdiag import get_classes, class_diagram
from sphinxcontrib.mermaid.exceptions import MermaidError
from docutils.parsers.rst import directives


# Test 1: align_spec validation property
@given(st.text())
def test_align_spec_only_accepts_valid_values(input_text):
    """
    align_spec should only accept "left", "center", or "right" and raise
    exception for any other value. This is a contract property.
    """
    valid_values = ["left", "center", "right"]
    
    if input_text in valid_values:
        result = align_spec(input_text)
        assert result == input_text
    else:
        # directives.choice raises ValueError for invalid choices
        with pytest.raises(ValueError):
            align_spec(input_text)


# Test 2: Class diagram generation properties
@composite
def class_names(draw):
    """Generate valid Python class names"""
    first_char = draw(st.sampled_from('ABCDEFGHIJKLMNOPQRSTUVWXYZ'))
    rest = draw(st.text(alphabet='ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_', min_size=0, max_size=10))
    return first_char + rest


@given(st.lists(class_names(), min_size=0, max_size=5))
def test_class_diagram_empty_when_no_inheritance(class_names_list):
    """
    class_diagram should return empty string when classes have no inheritance
    (other than object). This tests the documented behavior.
    """
    # Create independent classes dynamically
    module = types.ModuleType("test_module")
    module.__name__ = "test_module"
    
    for name in class_names_list:
        # Create class with no base (implicitly inherits from object)
        cls = type(name, (), {})
        cls.__module__ = "test_module"
        setattr(module, name, cls)
    
    # Store module to make it importable
    sys.modules["test_module"] = module
    
    try:
        # Test with classes that only inherit from object
        result = class_diagram("test_module", strict=False)
        assert result == "", f"Expected empty string for classes with no inheritance, got: {result}"
    finally:
        del sys.modules["test_module"]


@given(st.lists(st.tuples(class_names(), class_names()), min_size=1, max_size=5))
def test_class_diagram_inheritance_format(inheritance_pairs):
    """
    class_diagram should generate valid Mermaid classDiagram syntax
    when there are inheritance relationships.
    """
    # Filter out self-inheritance
    inheritance_pairs = [(parent, child) for parent, child in inheritance_pairs if parent != child]
    
    if not inheritance_pairs:
        return  # Skip if no valid pairs
    
    module = types.ModuleType("test_module")
    module.__name__ = "test_module"
    
    # Create all unique class names
    all_classes = set()
    for parent, child in inheritance_pairs:
        all_classes.add(parent)
        all_classes.add(child)
    
    # Create base classes first
    created_classes = {}
    for name in all_classes:
        cls = type(name, (), {})
        cls.__module__ = "test_module"
        created_classes[name] = cls
        setattr(module, name, cls)
    
    # Now create inheritance relationships
    for parent, child in inheritance_pairs:
        # Recreate child class with parent as base
        parent_cls = created_classes[parent]
        child_cls = type(child, (parent_cls,), {})
        child_cls.__module__ = "test_module"
        created_classes[child] = child_cls
        setattr(module, child, child_cls)
    
    sys.modules["test_module"] = module
    
    try:
        result = class_diagram("test_module", strict=False)
        
        if result:
            # Verify format
            lines = result.strip().split('\n')
            assert lines[0] == "classDiagram", f"First line should be 'classDiagram', got: {lines[0]}"
            
            # Check inheritance lines format
            for line in lines[1:]:
                assert line.startswith("  "), f"Inheritance lines should be indented: {line}"
                assert " <|-- " in line, f"Line should contain ' <|-- ': {line}"
    finally:
        del sys.modules["test_module"]


# Test 3: SHA1 hash determinism property
@given(
    st.text(min_size=1, max_size=100),
    st.dictionaries(st.text(min_size=1, max_size=10), st.text(min_size=1, max_size=10)),
    st.one_of(st.none(), st.text())
)
@settings(max_examples=100)
def test_hash_determinism(code, options, sequence_config):
    """
    Test that the hash generation is deterministic - same inputs always
    produce same hash. This is critical for caching behavior.
    """
    # Simulate the hash generation from render_mm
    hashkey1 = (code + str(options) + str(sequence_config)).encode("utf-8")
    hash1 = hashlib.sha1(hashkey1).hexdigest()
    
    # Generate hash again with same inputs
    hashkey2 = (code + str(options) + str(sequence_config)).encode("utf-8")
    hash2 = hashlib.sha1(hashkey2).hexdigest()
    
    assert hash1 == hash2, "Hash should be deterministic for same inputs"
    
    # Test that different inputs produce different hashes
    if len(code) > 1:
        modified_code = code[:-1] if code else "x"
        hashkey3 = (modified_code + str(options) + str(sequence_config)).encode("utf-8")
        hash3 = hashlib.sha1(hashkey3).hexdigest()
        assert hash1 != hash3, "Different inputs should produce different hashes"


# Test 4: get_classes module vs class handling
@given(st.sampled_from(["module", "class", "function", "variable"]))
def test_get_classes_type_handling(obj_type):
    """
    Test that get_classes correctly handles different object types:
    - Classes should be yielded
    - Modules should have their classes extracted
    - Other types should raise MermaidError
    """
    module = types.ModuleType("test_module")
    module.__name__ = "test_module"
    
    # Create test class
    TestClass = type("TestClass", (), {})
    TestClass.__module__ = "test_module"
    module.TestClass = TestClass
    
    # Create test function
    def test_func():
        pass
    module.test_func = test_func
    
    # Create test variable
    module.test_var = 42
    
    sys.modules["test_module"] = module
    
    try:
        if obj_type == "module":
            # Should extract classes from module
            result = list(get_classes("test_module"))
            assert len(result) == 1
            assert result[0].__name__ == "TestClass"
        
        elif obj_type == "class":
            # Should yield the class itself
            result = list(get_classes("test_module.TestClass"))
            assert len(result) == 1
            assert result[0].__name__ == "TestClass"
        
        elif obj_type == "function":
            # Should raise MermaidError for non-class/module
            with pytest.raises(MermaidError, match="is not a class nor a module"):
                list(get_classes("test_module.test_func"))
        
        elif obj_type == "variable":
            # Should raise MermaidError for non-class/module
            with pytest.raises(MermaidError, match="is not a class nor a module"):
                list(get_classes("test_module.test_var"))
    
    finally:
        del sys.modules["test_module"]


# Test 5: strict mode property for get_classes
@given(st.booleans())
def test_get_classes_strict_mode(strict):
    """
    Test that strict mode correctly filters classes:
    - strict=True: only classes defined in the module
    - strict=False: all classes including imported ones
    """
    # Create main module
    module = types.ModuleType("test_module")
    module.__name__ = "test_module"
    
    # Create a class defined in the module
    LocalClass = type("LocalClass", (), {})
    LocalClass.__module__ = "test_module"
    module.LocalClass = LocalClass
    
    # Create an imported class (from different module)
    ImportedClass = type("ImportedClass", (), {})
    ImportedClass.__module__ = "other_module"
    module.ImportedClass = ImportedClass
    
    sys.modules["test_module"] = module
    
    try:
        result = list(get_classes("test_module", strict=strict))
        
        if strict:
            # Should only include LocalClass
            assert len(result) == 1
            assert result[0].__name__ == "LocalClass"
        else:
            # Should include both classes
            assert len(result) == 2
            class_names = {cls.__name__ for cls in result}
            assert class_names == {"LocalClass", "ImportedClass"}
    
    finally:
        del sys.modules["test_module"]


# Test 6: Edge case - multiple inheritance in class_diagram
def test_class_diagram_multiple_inheritance():
    """
    Test that class_diagram correctly handles multiple inheritance.
    """
    module = types.ModuleType("test_module")
    module.__name__ = "test_module"
    
    # Create base classes
    BaseA = type("BaseA", (), {})
    BaseA.__module__ = "test_module"
    module.BaseA = BaseA
    
    BaseB = type("BaseB", (), {})
    BaseB.__module__ = "test_module"
    module.BaseB = BaseB
    
    # Create child with multiple inheritance
    Child = type("Child", (BaseA, BaseB), {})
    Child.__module__ = "test_module"
    module.Child = Child
    
    sys.modules["test_module"] = module
    
    try:
        result = class_diagram("test_module.Child", full=False)
        
        # Should contain both inheritance relationships
        assert "BaseA <|-- Child" in result
        assert "BaseB <|-- Child" in result
        assert result.startswith("classDiagram\n")
    
    finally:
        del sys.modules["test_module"]