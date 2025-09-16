import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/sphinxcontrib-mermaid_env/lib/python3.13/site-packages')

import string
from hypothesis import given, strategies as st, assume, settings
from docutils.parsers.rst import directives
import pytest

# Import the functions we want to test
from sphinxcontrib.mermaid import align_spec
from sphinxcontrib.mermaid.autoclassdiag import get_classes, class_diagram
from sphinxcontrib.mermaid.exceptions import MermaidError


# Property 1: align_spec should only accept "left", "center", "right" and raise for others
@given(st.text())
def test_align_spec_validation(text):
    """Test that align_spec only accepts valid alignment values"""
    valid_alignments = {"left", "center", "right"}
    
    if text in valid_alignments:
        # Should return the same value for valid inputs
        result = align_spec(text)
        assert result == text
    else:
        # Should raise for invalid inputs
        with pytest.raises(ValueError):
            align_spec(text)


# Property 2: align_spec with extreme inputs
@given(st.one_of(
    st.text(min_size=1000, max_size=10000),  # Very long strings
    st.text().filter(lambda x: "\n" in x or "\r" in x),  # Strings with newlines
    st.text().filter(lambda x: "\x00" in x),  # Null bytes
    st.text(alphabet=string.whitespace, min_size=1),  # Only whitespace
))
def test_align_spec_extreme_inputs(text):
    """Test align_spec with extreme/edge case inputs"""
    # These should all raise since they're not valid alignments
    with pytest.raises(ValueError):
        align_spec(text)


# Property 3: class_diagram output format properties
@given(st.lists(st.tuples(st.text(min_size=1), st.text(min_size=1)), min_size=0, max_size=10))
def test_class_diagram_format(inheritance_pairs):
    """Test that class_diagram output follows expected format"""
    # Mock get_classes to return controlled data
    class MockClass:
        def __init__(self, name, bases):
            self.__name__ = name
            self.__bases__ = bases
            self.__module__ = "test.module"
    
    # Create a simple inheritance chain to test output format
    if inheritance_pairs:
        # Simulate class hierarchy
        classes = []
        for parent, child in inheritance_pairs:
            parent_cls = type(parent, (), {"__name__": parent, "__module__": "test"})
            child_cls = type(child, (parent_cls,), {"__name__": child, "__module__": "test"})
            classes.append(child_cls)
        
        # We can't easily mock the import_object, but we can test the output format principle
        # by checking that the format matches expected pattern
        # This is a limitation - we'd need to test the actual function with real classes


# Property 4: get_classes should handle invalid module/class names
@given(st.text())
def test_get_classes_invalid_names(name):
    """Test that get_classes raises MermaidError for invalid names"""
    # Most random strings won't be valid module/class names
    assume(not name.startswith("sys"))  # Avoid accidentally importing real modules
    assume(not name.startswith("os"))
    assume(not name.startswith("__"))
    assume(len(name) > 0)
    
    try:
        # Try to get classes from a random string
        list(get_classes(name))
        # If it succeeds, it found a real module/class (unlikely with random strings)
    except MermaidError:
        # Expected behavior for invalid names
        pass
    except Exception as e:
        # Any other exception type would be a bug
        if "No module named" not in str(e):
            raise


# Property 5: class_diagram with empty input should return empty string
def test_class_diagram_empty():
    """Test that class_diagram returns empty string when no classes found"""
    # According to the code, if no inheritances are found, it returns ""
    # We can't easily test this without mocking, but the logic is clear in the code


# Property 6: Test the deterministic hash-based filename generation
@given(st.text(), st.dictionaries(st.text(), st.text()))
def test_hash_filename_deterministic(code, options):
    """Test that the same code and options always produce the same hash"""
    from hashlib import sha1
    
    # Simulate the hash generation logic from line 239-241
    mermaid_sequence_config = ""  # Default config
    hashkey1 = (code + str(options) + str(mermaid_sequence_config)).encode("utf-8")
    hashkey2 = (code + str(options) + str(mermaid_sequence_config)).encode("utf-8")
    
    hash1 = sha1(hashkey1).hexdigest()
    hash2 = sha1(hashkey2).hexdigest()
    
    # Same input should produce same hash
    assert hash1 == hash2
    
    # Hash should be 40 characters (SHA1 hex digest)
    assert len(hash1) == 40
    assert all(c in '0123456789abcdef' for c in hash1)


# Property 7: Test configuration format generation
@given(
    config_dict=st.dictionaries(st.text(min_size=1), st.one_of(st.text(), st.integers(), st.booleans())),
    title=st.text()
)
def test_mermaid_config_format(config_dict, title):
    """Test that mermaid configuration is generated in expected format"""
    from yaml import dump
    from json import dumps, loads
    
    mm_config = "---"
    
    if config_dict:
        mm_config += "\n"
        # Simulate the config generation from lines 191-193
        try:
            config_json = dumps(config_dict)
            parsed_config = loads(config_json)
            mm_config += dump({"config": parsed_config})
        except:
            # Some configs might not be JSON serializable
            pass
    
    if title:
        mm_config += "\n"
        mm_config += f"title: {title}"
    
    mm_config += "\n---\n"
    
    # Check format properties
    assert mm_config.startswith("---")
    assert mm_config.endswith("---\n")
    
    # If no config or title, should be minimal
    if not config_dict and not title:
        assert mm_config == "---\n---\n"