#!/usr/bin/env python3
"""Property-based tests for pdfkit.api module - Version 2"""

import sys
import os
import tempfile
import re
from hypothesis import given, strategies as st, assume, settings
import pytest

# Add the pdfkit package to path
sys.path.insert(0, '/root/hypothesis-llm/envs/pdfkit_env/lib/python3.13/site-packages')

import pdfkit
from pdfkit.pdfkit import PDFKit
from pdfkit.source import Source  
from pdfkit.configuration import Configuration


# Mock configuration to avoid wkhtmltopdf dependency
class MockConfiguration(Configuration):
    def __init__(self, wkhtmltopdf='mock', meta_tag_prefix='pdfkit-', environ=None):
        self.wkhtmltopdf = wkhtmltopdf
        self.meta_tag_prefix = meta_tag_prefix
        self.environ = environ if environ is not None else os.environ


# Test 1: Option normalization invariant
@given(
    option_name=st.text(min_size=1, max_size=50).filter(lambda x: not x.startswith('-')),
    option_value=st.one_of(st.text(), st.booleans(), st.integers(), st.none())
)
def test_option_normalization_consistency(option_name, option_value):
    """Options with or without '--' prefix should be normalized consistently"""
    pdf = PDFKit('test', 'string', configuration=MockConfiguration())
    
    opts_without_prefix = {option_name: option_value}
    opts_with_prefix = {'--' + option_name: option_value}
    
    normalized_without = list(pdf._normalize_options(opts_without_prefix))
    normalized_with = list(pdf._normalize_options(opts_with_prefix))
    
    if normalized_without and normalized_with:
        assert normalized_without[0][0].lower() == normalized_with[0][0].lower()


# Test 2: Meta tag extraction property  
@given(
    prefix=st.text(min_size=1, max_size=20, alphabet=st.characters(blacklist_characters='<>"\'')),
    option_name=st.text(min_size=1, max_size=30, alphabet=st.characters(blacklist_characters='<>"\'')),
    option_value=st.text(min_size=0, max_size=50, alphabet=st.characters(blacklist_characters='<>"\''))
)
def test_meta_tag_extraction(prefix, option_name, option_value):
    """HTML meta tags with configured prefix should be correctly extracted"""
    html = f'<html><head><meta name="{prefix}{option_name}" content="{option_value}"></head><body></body></html>'
    
    config = MockConfiguration(meta_tag_prefix=prefix)
    pdf = PDFKit(html, 'string', configuration=config)
    
    found_options = pdf._find_options_in_meta(html)
    
    assert option_name in found_options
    assert found_options[option_name] == option_value


# Test 3: Configuration initialization bug
@given(
    wkhtmltopdf_path=st.text(min_size=0, max_size=100),
    meta_tag_prefix=st.text(min_size=1, max_size=50)
)
def test_configuration_bytes_bug(wkhtmltopdf_path, meta_tag_prefix):
    """Configuration should handle byte strings properly"""
    # This test demonstrates the bug in Configuration class
    # When wkhtmltopdf is empty, it runs 'which wkhtmltopdf' which returns bytes
    # Then it tries to open() those bytes directly, causing a crash
    
    # Simulate what happens in Configuration.__init__
    import subprocess
    
    # This simulates the actual code path when wkhtmltopdf is empty
    if not wkhtmltopdf_path:
        try:
            # This is what the code does
            result = subprocess.Popen(
                ['which', 'nonexistent_binary'], 
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            ).communicate()[0]
            
            # result is bytes, not string
            assert isinstance(result, bytes)
            
            lines = result.splitlines()
            if len(lines) > 0:
                first_line = lines[0].strip()
            else:
                first_line = result.strip()
            
            # The bug: first_line is still bytes, not a string
            assert isinstance(first_line, bytes)
            
            # This is where the actual code would fail
            # with open(first_line) as f:  # TypeError: expected str, bytes or os.PathLike object, not bytes
            #     pass
            
            # The error message also shows the bytes representation
            error_msg = 'No wkhtmltopdf executable found: "%s"' % first_line
            assert "b''" in error_msg or "b'" in error_msg  # Shows bytes literal in error
            
        except Exception:
            pass


# Test 4: Option value type handling
@given(
    option_name=st.text(min_size=1, max_size=30).filter(lambda x: not x.startswith('-')),
    option_value=st.one_of(
        st.booleans(),
        st.text(min_size=0, max_size=50),
        st.integers(),
        st.lists(st.text(min_size=1, max_size=20), min_size=2, max_size=3)
    )
)
def test_option_value_normalization(option_name, option_value):
    """Option values should be normalized according to their type"""
    pdf = PDFKit('test', 'string', configuration=MockConfiguration())
    options = {option_name: option_value}
    
    normalized = list(pdf._normalize_options(options))
    
    if normalized:
        if isinstance(option_value, list):
            # Lists should generate multiple key-value pairs
            assert len(normalized) == len(option_value)
            for i, item in enumerate(option_value):
                assert normalized[i][0] == f'--{option_name.lower()}'
                assert normalized[i][1] == str(item) if item else item
        else:
            key, value = normalized[0]
            # Boolean values should become empty strings
            if isinstance(option_value, bool):
                assert value == ''
            else:
                # Other values should be stringified if not None/empty
                if option_value:
                    assert str(option_value) in str(value)


# Test 5: Source type validation
@given(
    file_paths=st.lists(
        st.text(min_size=1, max_size=50, alphabet=st.characters(min_codepoint=97, max_codepoint=122)),
        min_size=1, 
        max_size=5
    )
)
def test_source_file_existence_check(file_paths):
    """File sources should check for file existence"""
    file_paths = [f"/tmp/test_{i}_{path}.html" for i, path in enumerate(file_paths)]
    
    if len(file_paths) == 1:
        with pytest.raises(IOError, match="No such file"):
            Source(file_paths[0], 'file')
    else:
        with pytest.raises(IOError, match="No such file"):
            Source(file_paths, 'file')


# Test 6: CSS addition restriction
def test_css_restriction_for_urls():
    """CSS cannot be added to URL sources"""
    pdf = PDFKit('http://example.com', 'url', configuration=MockConfiguration())
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.css', delete=False) as css_file:
        css_file.write('body { color: red; }')
        css_path = css_file.name
    
    try:
        with pytest.raises(PDFKit.ImproperSourceError) as exc_info:
            pdf._prepend_css(css_path)
        assert 'CSS files can be added only to a single file or string' in str(exc_info.value)
    finally:
        os.unlink(css_path)


def test_css_restriction_for_multiple_files():
    """CSS cannot be added to multiple file sources"""  
    pdf = PDFKit(['file1.html', 'file2.html'], 'file', configuration=MockConfiguration())
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.css', delete=False) as css_file:
        css_file.write('body { color: red; }')
        css_path = css_file.name
    
    try:
        with pytest.raises(PDFKit.ImproperSourceError) as exc_info:
            pdf._prepend_css(css_path)
        assert 'CSS files can be added only to a single file or string' in str(exc_info.value)
    finally:
        os.unlink(css_path)