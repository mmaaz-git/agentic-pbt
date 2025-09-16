#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
import tempfile
import io
from hypothesis import given, assume, strategies as st, settings
import random
import string
import shutil

# Add pdfkit to path
sys.path.insert(0, '/root/hypothesis-llm/envs/pdfkit_env/lib/python3.13/site-packages')

from pdfkit.source import Source

# Strategy for valid types
valid_types = st.sampled_from(['url', 'file', 'string'])

# Strategy for generating file paths
def temp_file_path():
    """Generate a temporary file path"""
    return tempfile.mktemp(suffix='.html')

# Property 1: File existence validation
@given(
    file_paths=st.lists(st.text(min_size=1), min_size=1, max_size=10),
    create_files=st.lists(st.booleans(), min_size=1, max_size=10)
)
def test_file_existence_validation(file_paths, create_files):
    """Test that Source with type='file' validates file existence correctly"""
    # Ensure same length
    create_files = create_files[:len(file_paths)]
    if len(create_files) < len(file_paths):
        create_files.extend([False] * (len(file_paths) - len(create_files)))
    
    temp_dir = tempfile.mkdtemp()
    try:
        # Create absolute paths
        abs_paths = []
        for i, path in enumerate(file_paths):
            # Clean the path to avoid directory traversal
            clean_path = ''.join(c for c in path if c.isalnum() or c in ('-', '_', '.'))
            if not clean_path:
                clean_path = f"file_{i}.html"
            abs_path = os.path.join(temp_dir, clean_path)
            abs_paths.append(abs_path)
            
            if create_files[i]:
                # Create the file
                with open(abs_path, 'w') as f:
                    f.write('<html></html>')
        
        # Test single file
        if len(abs_paths) == 1:
            if create_files[0]:
                # Should not raise error
                source = Source(abs_paths[0], 'file')
                assert source.source == abs_paths[0]
            else:
                # Should raise IOError for non-existent file
                try:
                    source = Source(abs_paths[0], 'file')
                    assert False, "Should have raised IOError for non-existent file"
                except IOError as e:
                    assert 'No such file' in str(e)
        
        # Test list of files
        else:
            if all(create_files):
                # All files exist, should not raise
                source = Source(abs_paths, 'file')
                assert source.source == abs_paths
            else:
                # At least one file doesn't exist, should raise IOError
                try:
                    source = Source(abs_paths, 'file')
                    assert False, "Should have raised IOError for non-existent files"
                except IOError as e:
                    assert 'No such file' in str(e)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

# Property 2: Type method consistency
@given(
    type_=valid_types,
    source=st.text()
)
def test_type_method_consistency(type_, source):
    """Test that type checking methods return correct values based on type"""
    s = Source(source, type_)
    
    # Only one should be True
    url_check = s.isUrl()
    file_check = s.isFile()
    string_check = s.isString()
    
    if type_ == 'url':
        assert url_check == True
        assert file_check == False
        assert string_check == False
    elif type_ == 'file':
        assert url_check == False
        assert file_check == True
        assert string_check == False
    elif type_ == 'string':
        assert url_check == False
        assert file_check == False
        assert string_check == True

# Property 3: Unicode/string handling in to_s()
@given(
    input_str=st.text(),
    use_bytes=st.booleans()
)
def test_to_s_always_returns_unicode(input_str, use_bytes):
    """Test that to_s() always returns unicode/str type"""
    if use_bytes:
        # Convert to bytes
        try:
            source_input = input_str.encode('utf-8')
        except:
            # Skip if encoding fails
            assume(False)
    else:
        source_input = input_str
    
    s = Source(source_input, 'string')
    result = s.to_s()
    
    # Check that result is always str (unicode in Python 3)
    assert isinstance(result, str), f"Expected str, got {type(result)}"
    
    # If input was string, it should be preserved
    if not use_bytes:
        assert result == input_str

# Property 4: File object detection
@given(
    has_read_method=st.booleans(),
    other_attrs=st.lists(st.text(min_size=1, max_size=10), max_size=5)
)
def test_file_object_detection(has_read_method, other_attrs):
    """Test that isFileObj correctly identifies objects with read method"""
    
    class TestObj:
        pass
    
    obj = TestObj()
    
    # Add other attributes
    for attr in other_attrs:
        setattr(obj, attr, lambda: None)
    
    # Add read method if specified
    if has_read_method:
        obj.read = lambda: b"test"
    
    s = Source(obj, 'file')
    
    # Test isFileObj
    assert s.isFileObj() == has_read_method

# Property 5: Test behavior with file-like objects in checkFiles
@given(
    content=st.binary(min_size=0, max_size=1000)
)
def test_file_like_object_no_exception(content):
    """Test that file-like objects don't raise exceptions in checkFiles"""
    file_obj = io.BytesIO(content)
    
    # This should not raise an exception
    s = Source(file_obj, 'file')
    
    # File object should be detected
    assert s.isFileObj() == True
    
    # Should not be treated as a regular file path
    assert hasattr(s.source, 'read')

# Property 6: Type parameter affects behavior
@given(
    source=st.text(),
    type1=valid_types,
    type2=valid_types
)
def test_type_parameter_consistency(source, type1, type2):
    """Test that the type parameter consistently affects object behavior"""
    s1 = Source(source, type1)
    s2 = Source(source, type2)
    
    # If types are the same, behavior should be identical
    if type1 == type2:
        assert s1.isUrl() == s2.isUrl()
        assert s1.isFile() == s2.isFile()
        assert s1.isString() == s2.isString()
    else:
        # Different types should have different behavior
        assert (s1.isUrl() != s2.isUrl()) or (s1.isFile() != s2.isFile()) or (s1.isString() != s2.isString())

# Property 7: Edge case - empty string handling
@given(
    type_=valid_types
)
def test_empty_string_handling(type_):
    """Test handling of empty strings"""
    s = Source("", type_)
    
    # Type methods should still work correctly
    if type_ == 'url':
        assert s.isUrl() == True
    elif type_ == 'file':
        assert s.isFile() == True
    elif type_ == 'string':
        assert s.isString() == True
    
    # to_s should handle empty string
    if type_ == 'string':
        assert s.to_s() == ""

# Property 8: Test isFile with path parameter
@given(
    create_io_base=st.booleans(),
    create_stream_reader=st.booleans()
)
def test_isFile_with_path_parameter(create_io_base, create_stream_reader):
    """Test isFile method with path parameter for different object types"""
    
    if create_io_base:
        path_obj = io.BytesIO(b"test")
        expected = True
    elif create_stream_reader:
        # Simulate StreamReaderWriter-like object
        class StreamReaderWriter:
            pass
        path_obj = StreamReaderWriter()
        expected = True
    else:
        path_obj = "regular_string"
        expected = False
    
    s = Source("dummy", "file")
    
    # Test isFile with path parameter
    result = s.isFile(path=path_obj)
    assert result == expected

if __name__ == "__main__":
    import pytest
    # Run with increased examples for thorough testing
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])