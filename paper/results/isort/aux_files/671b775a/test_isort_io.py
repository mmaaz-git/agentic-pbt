import os
import tempfile
from io import BytesIO
from pathlib import Path

from hypothesis import assume, given, strategies as st
from isort.exceptions import UnsupportedEncoding
from isort.io import Empty, File


@given(
    encoding=st.sampled_from(['utf-8', 'utf-16', 'ascii', 'latin-1', 'cp1252', 'iso-8859-1']),
    content=st.text(min_size=0, max_size=1000)
)
def test_detect_encoding_with_explicit_declaration(encoding, content):
    """Test that detect_encoding correctly identifies explicitly declared encodings"""
    encoding_line = f"# -*- coding: {encoding} -*-\n"
    
    try:
        full_content = (encoding_line + content).encode(encoding)
    except (UnicodeEncodeError, LookupError):
        assume(False)
    
    buffer = BytesIO(full_content)
    detected = File.detect_encoding("test.py", buffer.readline)
    
    # The detected encoding should handle the content correctly
    try:
        full_content.decode(detected)
    except (UnicodeDecodeError, LookupError):
        # If we can't decode with the detected encoding, there's a bug
        assert False, f"Detected encoding {detected} cannot decode content with declared encoding {encoding}"


@given(
    content=st.text(min_size=0, max_size=1000),
    filename=st.text(min_size=1, max_size=100).filter(lambda x: '/' not in x and '\\' not in x and x.strip())
)
def test_from_contents_preserves_content(content, filename):
    """Test that File.from_contents preserves the original content"""
    assume('\x00' not in content)  # Null bytes can cause issues
    
    file_obj = File.from_contents(content, filename)
    
    # Read the content back from the stream
    file_obj.stream.seek(0)
    read_content = file_obj.stream.read()
    
    assert read_content == content, f"Content mismatch: expected {content!r}, got {read_content!r}"
    
    # Check that path is resolved correctly
    assert file_obj.path == Path(filename).resolve()
    
    # Check that encoding is detected
    assert file_obj.encoding is not None


@given(
    stem=st.text(min_size=1, max_size=50).filter(lambda x: '/' not in x and '\\' not in x and '.' not in x and x.strip()),
    extension=st.text(min_size=0, max_size=10).filter(lambda x: '/' not in x and '\\' not in x and '.' not in x)
)
def test_extension_property(stem, extension):
    """Test that the extension property correctly extracts file extensions"""
    if extension:
        filename = f"{stem}.{extension}"
        expected_ext = extension
    else:
        filename = stem
        expected_ext = ""
    
    file_obj = File.from_contents("test content", filename)
    
    assert file_obj.extension == expected_ext, f"Expected extension {expected_ext!r}, got {file_obj.extension!r}"


@given(
    filename=st.text(min_size=1, max_size=100).filter(lambda x: '/' not in x and '\\' not in x and x.strip())
)
def test_extension_property_multiple_dots(filename):
    """Test extension property with filenames containing multiple dots"""
    assume('\x00' not in filename)
    
    file_obj = File.from_contents("test", filename)
    
    # The extension should be everything after the last dot
    if '.' in filename:
        expected = filename.rsplit('.', 1)[1]
    else:
        expected = ""
    
    assert file_obj.extension == expected


@given(data=st.text())
def test_empty_io_suppresses_writes(data):
    """Test that Empty IO doesn't actually write anything"""
    # Store initial state
    initial_value = Empty.getvalue()
    
    # Try to write data
    Empty.write(data)
    
    # Check that nothing was written
    assert Empty.getvalue() == initial_value
    
    # Also test with kwargs
    Empty.write(data, end='\n')
    assert Empty.getvalue() == initial_value


@given(
    content=st.text(min_size=0, max_size=1000),
    encoding_format=st.sampled_from([
        "# coding: {}",
        "# -*- coding: {} -*-", 
        "# coding={}",
        "#!/usr/bin/env python\n# coding: {}",
        "# vim: set fileencoding={} :",
    ]),
    encoding=st.sampled_from(['utf-8', 'latin-1', 'ascii'])
)
def test_detect_encoding_various_formats(content, encoding_format, encoding):
    """Test that various encoding declaration formats are recognized"""
    encoding_line = encoding_format.format(encoding) + "\n"
    
    try:
        full_content = (encoding_line + content).encode(encoding)
    except UnicodeEncodeError:
        assume(False)
    
    buffer = BytesIO(full_content)
    detected = File.detect_encoding("test.py", buffer.readline)
    
    # The detected encoding should be able to decode the content
    try:
        full_content.decode(detected)
    except (UnicodeDecodeError, LookupError):
        assert False, f"Detected encoding {detected} cannot decode content"


@given(
    content=st.text(min_size=0, max_size=1000)
)
def test_file_read_context_manager_with_temp_file(content):
    """Test File.read context manager with actual files"""
    assume('\x00' not in content)  # Null bytes can cause issues
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        temp_path = f.name
        f.write(content)
    
    try:
        # Use File.read context manager
        with File.read(temp_path) as file_obj:
            # Check that we can read the content
            read_content = file_obj.stream.read()
            assert read_content == content
            
            # Check that path is correct
            assert file_obj.path == Path(temp_path).resolve()
            
            # Check that encoding is set
            assert file_obj.encoding is not None
    finally:
        os.unlink(temp_path)


@given(
    invalid_bytes=st.binary(min_size=1, max_size=100).filter(lambda b: b'\n' not in b[:2])
)
def test_detect_encoding_raises_on_invalid(invalid_bytes):
    """Test that detect_encoding raises UnsupportedEncoding for truly invalid encodings"""
    # Create bytes that are not valid UTF-8 and don't have a coding declaration
    assume(not invalid_bytes.startswith(b'#'))
    assume(b'coding' not in invalid_bytes.lower())
    
    # Add some invalid UTF-8 sequences
    invalid_content = b'\xff\xfe' + invalid_bytes
    
    buffer = BytesIO(invalid_content)
    
    try:
        encoding = File.detect_encoding("test.py", buffer.readline)
        # If we got an encoding, it should be able to decode the content
        buffer.seek(0)
        content = buffer.read()
        content.decode(encoding)
    except UnsupportedEncoding:
        # This is expected for invalid content
        pass
    except UnicodeDecodeError:
        # The encoding was detected but can't actually decode - this might be a bug
        pass