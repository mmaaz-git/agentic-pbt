"""Property-based tests for Cython.Debugger module"""

import os
import tempfile
import xml.etree.ElementTree as ET
from hypothesis import given, strategies as st, assume, settings
import Cython.Debugger.DebugWriter as DebugWriter
import Cython.Debugger.Cygdb as Cygdb


# Test 1: is_valid_tag should correctly identify generator argument patterns
@given(st.integers(min_value=0, max_value=10000))
def test_is_valid_tag_generator_args(n):
    """Test that is_valid_tag correctly rejects generator argument patterns like '.0', '.1', etc."""
    # Create an EncodedString instance with generator pattern
    name = DebugWriter.EncodedString(f".{n}")
    result = DebugWriter.is_valid_tag(name)
    assert result is False, f"is_valid_tag should return False for '.{n}' but returned {result}"


# Test 2: is_valid_tag should accept non-generator patterns  
@given(st.text(min_size=1, max_size=100).filter(lambda x: not (x.startswith('.') and x[1:].isdecimal())))
def test_is_valid_tag_normal_names(name):
    """Test that is_valid_tag accepts normal names that aren't generator patterns"""
    encoded_name = DebugWriter.EncodedString(name)
    result = DebugWriter.is_valid_tag(encoded_name)
    assert result is True, f"is_valid_tag should return True for '{name}' but returned {result}"


# Test 3: EncodedString should preserve string behavior
@given(st.text(min_size=0, max_size=1000))
def test_encoded_string_is_string(text):
    """Test that EncodedString behaves like a normal string"""
    encoded = DebugWriter.EncodedString(text)
    # Should be equal to original string
    assert encoded == text
    # Should have same length
    assert len(encoded) == len(text)
    # Should be instance of str
    assert isinstance(encoded, str)
    # Should preserve string operations
    assert encoded.upper() == text.upper()
    assert encoded.lower() == text.lower()


# Test 4: CythonDebugWriter should produce valid XML
@given(
    st.lists(
        st.tuples(
            st.text(alphabet=st.characters(blacklist_categories=["Cs"], min_codepoint=1), min_size=1, max_size=20).filter(
                lambda x: x.isidentifier() and not x.startswith('.') 
            ),
            st.dictionaries(
                st.text(alphabet=st.characters(blacklist_categories=["Cs"], min_codepoint=1), min_size=1, max_size=10),
                st.text(alphabet=st.characters(blacklist_categories=["Cs"], min_codepoint=1), min_size=0, max_size=50),
                max_size=3
            )
        ),
        min_size=0,
        max_size=10
    )
)
def test_cython_debug_writer_xml_generation(entries):
    """Test that CythonDebugWriter produces well-formed XML"""
    with tempfile.TemporaryDirectory() as tmpdir:
        writer = DebugWriter.CythonDebugWriter(tmpdir)
        writer.module_name = "test_module"
        
        # Start a Module element
        writer.start('Module', {'name': 'test'})
        
        # Add entries
        for name, attrs in entries:
            # Convert dict values to strings (XML attributes must be strings)
            str_attrs = {k: str(v) for k, v in attrs.items()}
            writer.add_entry(name, **str_attrs)
        
        # Serialize the XML
        writer.serialize()
        
        # Check that the XML file was created
        xml_file = os.path.join(tmpdir, 'cython_debug', 'cython_debug_info_test_module')
        assert os.path.exists(xml_file), f"XML file not created at {xml_file}"
        
        # Try to parse the XML to verify it's well-formed
        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            assert root.tag == 'cython_debug'
            # Verify the structure
            modules = root.findall('Module')
            assert len(modules) == 1
        except ET.ParseError as e:
            assert False, f"Generated XML is not well-formed: {e}"


# Test 5: Test interaction between is_valid_tag and CythonDebugWriter
@given(st.text(min_size=1, max_size=50))
def test_debug_writer_filters_invalid_tags(name):
    """Test that CythonDebugWriter correctly filters tags based on is_valid_tag"""
    with tempfile.TemporaryDirectory() as tmpdir:
        writer = DebugWriter.CythonDebugWriter(tmpdir)
        writer.module_name = "test"
        
        # Convert to EncodedString to match actual usage
        encoded_name = DebugWriter.EncodedString(name)
        is_valid = DebugWriter.is_valid_tag(encoded_name)
        
        # Start Module
        writer.start('Module', {'name': 'test'})
        
        # Try to add an entry with this name
        writer.add_entry(name, value="test")
        
        # Serialize
        writer.serialize()
        
        # Parse the XML and check if the entry was added
        xml_file = os.path.join(tmpdir, 'cython_debug', 'cython_debug_info_test')
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        # Find all elements with our tag name
        found_elements = root.findall(f".//{name}")
        
        if is_valid:
            # Valid tags might be present (unless they conflict with XML rules)
            # We can't assert they're definitely there due to XML naming rules
            pass
        else:
            # Invalid tags should definitely not be there
            if name.startswith('.') and name[1:].isdecimal():
                assert len(found_elements) == 0, f"Invalid tag '{name}' should not appear in XML"


# Test 6: Test make_command_file creates readable files
@given(st.text(alphabet=st.characters(blacklist_categories=["Cc", "Cs"], min_codepoint=32), min_size=0, max_size=100))
def test_make_command_file_creates_file(prefix_code):
    """Test that make_command_file creates a readable file"""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a dummy debug info structure
        debug_dir = os.path.join(tmpdir, 'cython_debug')
        os.makedirs(debug_dir)
        
        # Create a dummy interpreter file
        with open(os.path.join(debug_dir, 'interpreter'), 'w') as f:
            f.write('/usr/bin/python3')
        
        # Create a dummy debug info file
        with open(os.path.join(debug_dir, 'cython_debug_info_test'), 'w') as f:
            f.write('<cython_debug></cython_debug>')
        
        # Call make_command_file
        result_file = Cygdb.make_command_file(tmpdir, prefix_code=prefix_code)
        
        # Check the file exists and is readable
        assert os.path.exists(result_file), f"Command file not created at {result_file}"
        assert os.path.isfile(result_file), f"Result is not a file: {result_file}"
        
        # Try to read the file
        with open(result_file, 'r') as f:
            content = f.read()
            
            # Check that prefix code is included
            assert prefix_code in content, f"Prefix code not found in command file"
            
            # Check for expected content
            assert 'set breakpoint pending on' in content
            assert 'from Cython.Debugger import libcython, libpython' in content
        
        # Clean up the temp file
        os.unlink(result_file)


# Test 7: EncodedString deepcopy behavior
@given(st.text(min_size=0, max_size=100))
def test_encoded_string_deepcopy(text):
    """Test that EncodedString.__deepcopy__ returns self (immutable behavior)"""
    import copy
    encoded = DebugWriter.EncodedString(text)
    copied = copy.deepcopy(encoded)
    # For immutable strings, deepcopy should return the same object
    assert copied is encoded, "EncodedString deepcopy should return self"
    assert copied == encoded, "Copied string should equal original"