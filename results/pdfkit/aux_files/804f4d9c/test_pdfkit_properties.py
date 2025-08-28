#!/usr/bin/env python3
"""Property-based tests for pdfkit.api module"""

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


# Test 1: Option normalization invariant
# Evidence: pdfkit.py lines 237-241 show that options with/without '--' should be normalized consistently
@given(
    option_name=st.text(min_size=1, max_size=50).filter(lambda x: not x.startswith('-')),
    option_value=st.one_of(st.text(), st.booleans(), st.integers(), st.none())
)
def test_option_normalization_consistency(option_name, option_value):
    """Options with or without '--' prefix should be normalized consistently"""
    # Create PDFKit instance with mock data
    pdf = PDFKit('test', 'string')
    
    # Test normalization with and without '--' prefix
    opts_without_prefix = {option_name: option_value}
    opts_with_prefix = {'--' + option_name: option_value}
    
    normalized_without = list(pdf._normalize_options(opts_without_prefix))
    normalized_with = list(pdf._normalize_options(opts_with_prefix))
    
    # Both should produce the same normalized key (with '--' and lowercase)
    if normalized_without and normalized_with:
        assert normalized_without[0][0].lower() == normalized_with[0][0].lower()


# Test 2: CSS addition restriction property
# Evidence: pdfkit.py lines 257-259 explicitly state CSS can only be added to single file or string
@given(
    source_type=st.sampled_from(['url', 'file', 'string']),
    is_list=st.booleans()
)  
def test_css_addition_restriction(source_type, is_list):
    """CSS files can only be added to single file or string sources"""
    if source_type == 'url':
        source = 'http://example.com' if not is_list else ['http://example.com', 'http://test.com']
    elif source_type == 'file':
        source = 'test.html' if not is_list else ['test1.html', 'test2.html']
    else:  # string
        source = '<html></html>'
    
    pdf = PDFKit(source, source_type)
    
    # According to the code, CSS addition should raise ImproperSourceError for:
    # 1. URL sources (any)
    # 2. List sources (multiple files)
    should_raise = (source_type == 'url') or (source_type == 'file' and is_list)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.css', delete=False) as css_file:
        css_file.write('body { color: red; }')
        css_path = css_file.name
    
    try:
        if should_raise:
            with pytest.raises(PDFKit.ImproperSourceError):
                pdf._prepend_css(css_path)
        else:
            # For single file sources, we need an actual file to exist
            if source_type == 'file':
                with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as html_file:
                    html_file.write('<html><head></head><body></body></html>')
                    pdf.source.source = html_file.name
                    
                try:
                    pdf._prepend_css(css_path)
                    # If no exception, the CSS was successfully prepended
                    assert pdf.source.isString()  # Source should be converted to string after CSS prepend
                finally:
                    os.unlink(html_file.name)
            else:  # string source
                pdf._prepend_css(css_path)
                assert '</style>' in pdf.source.to_s()  # CSS should be added as style tag
    finally:
        os.unlink(css_path)


# Test 3: Configuration kwargs preservation
# Evidence: configuration.py shows Configuration accepts wkhtmltopdf and meta_tag_prefix kwargs
@given(
    wkhtmltopdf_path=st.text(min_size=0, max_size=100),
    meta_tag_prefix=st.text(min_size=1, max_size=50)
)
def test_configuration_kwargs_preservation(wkhtmltopdf_path, meta_tag_prefix):
    """Configuration function should preserve the kwargs passed to it"""
    # The api.configuration function should pass kwargs through to Configuration class
    config = pdfkit.configuration(
        wkhtmltopdf=wkhtmltopdf_path,
        meta_tag_prefix=meta_tag_prefix
    )
    
    assert isinstance(config, Configuration)
    # Note: wkhtmltopdf might be modified if empty (it tries to find the binary)
    # but meta_tag_prefix should be preserved exactly
    assert config.meta_tag_prefix == meta_tag_prefix


# Test 4: Meta tag extraction property
# Evidence: pdfkit.py lines 298-302 show meta tag extraction logic
@given(
    prefix=st.text(min_size=1, max_size=20, alphabet=st.characters(blacklist_characters='<>"\'')),
    option_name=st.text(min_size=1, max_size=30, alphabet=st.characters(blacklist_characters='<>"\'')),
    option_value=st.text(min_size=0, max_size=50, alphabet=st.characters(blacklist_characters='<>"\''))
)
def test_meta_tag_extraction(prefix, option_name, option_value):
    """HTML meta tags with configured prefix should be correctly extracted"""
    # Create HTML with meta tag
    html = f'<html><head><meta name="{prefix}{option_name}" content="{option_value}"></head><body></body></html>'
    
    # Create PDFKit with custom configuration
    config = Configuration(meta_tag_prefix=prefix)
    pdf = PDFKit(html, 'string', configuration=config)
    
    # Extract options from meta tags
    found_options = pdf._find_options_in_meta(html)
    
    # The option should be found with the name (without prefix) as key
    assert option_name in found_options
    assert found_options[option_name] == option_value


# Test 5: Source file existence validation
# Evidence: source.py lines 33-40 show file existence checking
@given(
    file_paths=st.lists(
        st.text(min_size=1, max_size=50, alphabet=st.characters(min_codepoint=97, max_codepoint=122)),
        min_size=1, 
        max_size=5
    )
)
def test_source_file_existence_check(file_paths):
    """File sources should check for file existence"""
    # Add .html extension and make paths unique
    file_paths = [f"/tmp/test_{i}_{path}.html" for i, path in enumerate(file_paths)]
    
    # Single file case
    if len(file_paths) == 1:
        with pytest.raises(IOError, match="No such file"):
            Source(file_paths[0], 'file')
    
    # Multiple files case  
    else:
        with pytest.raises(IOError, match="No such file"):
            Source(file_paths, 'file')


# Test 6: Option value normalization
# Evidence: pdfkit.py line 247 shows special handling for boolean values
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
    pdf = PDFKit('test', 'string')
    options = {option_name: option_value}
    
    normalized = list(pdf._normalize_options(options))
    
    if normalized:
        key, value = normalized[0] if not isinstance(option_value, list) else normalized[0]
        
        # Boolean values should become empty strings
        if isinstance(option_value, bool):
            assert value == ''
        # Lists should generate multiple key-value pairs
        elif isinstance(option_value, list):
            assert len(normalized) == len(option_value)
            for i, item in enumerate(option_value):
                assert normalized[i][0] == f'--{option_name.lower()}'