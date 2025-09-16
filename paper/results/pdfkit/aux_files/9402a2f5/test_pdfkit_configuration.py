#!/usr/bin/env python3
"""Property-based tests for pdfkit.configuration.Configuration"""

import os
import sys
import tempfile
from hypothesis import given, strategies as st, assume, settings
import pytest

# Add the virtual environment's site-packages to path
sys.path.insert(0, '/root/hypothesis-llm/envs/pdfkit_env/lib/python3.13/site-packages')

from pdfkit.configuration import Configuration


# Strategy for environment dictionaries with various value types
@st.composite
def environ_dict(draw):
    """Generate environment dictionaries with various value types"""
    keys = draw(st.lists(
        st.text(min_size=1, max_size=20, alphabet=st.characters(blacklist_characters='\x00\n')),
        min_size=0,
        max_size=10,
        unique=True
    ))
    
    # Mix of different value types that might appear in environment variables
    values = []
    for _ in keys:
        value_type = draw(st.sampled_from(['string', 'int', 'float', 'bool', 'none', 'bytes']))
        if value_type == 'string':
            values.append(draw(st.text()))
        elif value_type == 'int':
            values.append(draw(st.integers()))
        elif value_type == 'float':
            values.append(draw(st.floats(allow_nan=False, allow_infinity=False)))
        elif value_type == 'bool':
            values.append(draw(st.booleans()))
        elif value_type == 'none':
            values.append(None)
        elif value_type == 'bytes':
            values.append(draw(st.binary()))
    
    return dict(zip(keys, values))


@given(
    meta_tag_prefix=st.text(),
    environ=environ_dict()
)
def test_environ_values_are_converted_to_strings(meta_tag_prefix, environ):
    """Test that all environment variable values are converted to strings"""
    
    # Create a temporary executable file to avoid the IOError
    with tempfile.NamedTemporaryFile(delete=False, mode='w') as f:
        f.write('#!/bin/sh\necho test')
        temp_path = f.name
    
    try:
        os.chmod(temp_path, 0o755)
        
        # Create configuration with our environment dict
        config = Configuration(
            wkhtmltopdf=temp_path,
            meta_tag_prefix=meta_tag_prefix,
            environ=environ
        )
        
        # Property: All values in config.environ should be strings
        for key, value in config.environ.items():
            assert isinstance(value, str), f"Value for key '{key}' is not a string: {type(value)}"
            
    finally:
        os.unlink(temp_path)


@given(
    meta_tag_prefix=st.text(min_size=0, max_size=100)
)
def test_meta_tag_prefix_preservation(meta_tag_prefix):
    """Test that meta_tag_prefix is preserved exactly as provided"""
    
    # Create a temporary executable file to avoid the IOError
    with tempfile.NamedTemporaryFile(delete=False, mode='w') as f:
        f.write('#!/bin/sh\necho test')
        temp_path = f.name
    
    try:
        os.chmod(temp_path, 0o755)
        
        config = Configuration(
            wkhtmltopdf=temp_path,
            meta_tag_prefix=meta_tag_prefix
        )
        
        # Property: meta_tag_prefix should be preserved exactly
        assert config.meta_tag_prefix == meta_tag_prefix
        
    finally:
        os.unlink(temp_path)


@given(
    use_bytes=st.booleans()
)
def test_binary_path_handling(use_bytes):
    """Test that Configuration handles both byte strings and regular strings for paths"""
    
    # Create a temporary executable file
    with tempfile.NamedTemporaryFile(delete=False, mode='w') as f:
        f.write('#!/bin/sh\necho test')
        temp_path = f.name
    
    try:
        os.chmod(temp_path, 0o755)
        
        if use_bytes:
            # Test with byte string path
            path = temp_path.encode('utf-8')
        else:
            # Test with regular string path
            path = temp_path
        
        config = Configuration(wkhtmltopdf=path)
        
        # Property: wkhtmltopdf should be accessible and valid regardless of input type
        assert config.wkhtmltopdf is not None
        # Check it's been properly handled (either kept as string or decoded from bytes)
        if isinstance(path, bytes):
            # If input was bytes, it should be decoded
            assert config.wkhtmltopdf == path.decode('utf-8').strip() or config.wkhtmltopdf == path
        else:
            # If input was string, it should be preserved
            assert config.wkhtmltopdf == path.strip() or config.wkhtmltopdf == path
            
    finally:
        os.unlink(temp_path)


@given(
    provide_environ=st.booleans(),
    environ=environ_dict()
)
def test_environ_default_handling(provide_environ, environ):
    """Test that environ defaults to os.environ when not provided"""
    
    # Create a temporary executable file
    with tempfile.NamedTemporaryFile(delete=False, mode='w') as f:
        f.write('#!/bin/sh\necho test')
        temp_path = f.name
    
    try:
        os.chmod(temp_path, 0o755)
        
        if provide_environ:
            config = Configuration(wkhtmltopdf=temp_path, environ=environ)
            # Property: When environ is provided, it should be used
            # All original keys should be present (though values are stringified)
            for key in environ.keys():
                assert key in config.environ
        else:
            config = Configuration(wkhtmltopdf=temp_path)
            # Property: When environ is not provided, os.environ should be used
            assert config.environ == os.environ
            
    finally:
        os.unlink(temp_path)


@given(
    wkhtmltopdf_path=st.one_of(
        st.none(),
        st.text(min_size=1, max_size=200),
        st.binary(min_size=1, max_size=200)
    )
)
def test_invalid_path_raises_ioerror(wkhtmltopdf_path):
    """Test that invalid paths raise IOError with appropriate message"""
    
    # Skip if the path accidentally points to a real file
    if wkhtmltopdf_path:
        try:
            # Check if it's a valid path that exists
            path_str = wkhtmltopdf_path.decode('utf-8') if isinstance(wkhtmltopdf_path, bytes) else wkhtmltopdf_path
            if os.path.exists(path_str):
                assume(False)  # Skip this test case
        except:
            pass  # Path is invalid, continue with test
    
    # Property: Invalid paths should raise IOError
    with pytest.raises(IOError) as exc_info:
        Configuration(wkhtmltopdf=wkhtmltopdf_path)
    
    # Check that the error message is appropriate
    assert 'No wkhtmltopdf executable found' in str(exc_info.value)


if __name__ == '__main__':
    # Run the tests
    pytest.main([__file__, '-v'])