import sys
import os
import re
from hypothesis import given, strategies as st, assume, settings
from collections import OrderedDict
import tempfile

sys.path.insert(0, '/root/hypothesis-llm/envs/pdfkit_env/lib/python3.13/site-packages')

import pdfkit
from pdfkit.pdfkit import PDFKit
from pdfkit.source import Source
from pdfkit.configuration import Configuration


@given(st.dictionaries(
    st.text(min_size=1, alphabet=st.characters(min_codepoint=33, max_codepoint=126, exclude_characters='-')),
    st.one_of(
        st.text(),
        st.booleans(),
        st.lists(st.text(), min_size=1, max_size=5),
        st.tuples(st.text(min_size=1), st.text(min_size=1))
    )
))
def test_option_normalization_adds_dashes(options):
    """Test that options without '--' get '--' prepended and are lowercased"""
    pdf = PDFKit('test.html', 'file')
    normalized = list(pdf._normalize_options(options))
    
    for key, _ in normalized:
        assert key.startswith('--'), f"Option key '{key}' should start with '--'"
        assert key == key.lower(), f"Option key '{key}' should be lowercased"


@given(st.dictionaries(
    st.text(min_size=1),
    st.booleans()
))
def test_boolean_options_become_empty_strings(options):
    """Test that boolean True values become empty strings in normalization"""
    pdf = PDFKit('test.html', 'file')
    normalized = list(pdf._normalize_options(options))
    
    for orig_key, orig_val in options.items():
        if orig_val is True:
            for norm_key, norm_val in normalized:
                if orig_key.lower() in norm_key.lower():
                    assert norm_val == '', f"Boolean True should become empty string, got '{norm_val}'"


@given(st.dictionaries(
    st.text(min_size=1),
    st.lists(st.text(), min_size=2, max_size=5)
))
def test_list_options_generate_multiple_pairs(options):
    """Test that list values generate multiple option pairs"""
    pdf = PDFKit('test.html', 'file')
    normalized = list(pdf._normalize_options(options))
    
    for key, value_list in options.items():
        if isinstance(value_list, list):
            normalized_key = '--' + key.lower() if '--' not in key else key.lower()
            count = sum(1 for k, _ in normalized if k == normalized_key)
            assert count == len(value_list), f"List with {len(value_list)} items should generate {len(value_list)} pairs, got {count}"


@given(st.text(min_size=1))
def test_source_type_exclusivity(content):
    """Test that a Source can only be one type"""
    source_url = Source(content, 'url')
    assert source_url.isUrl() and not source_url.isFile() and not source_url.isString()
    
    source_file = Source(content, 'file-like')  
    assert source_file.isFile() and not source_file.isUrl() and not source_file.isString()
    
    source_string = Source(content, 'string')
    assert source_string.isString() and not source_url.isFile() and not source_string.isUrl()


@given(st.lists(st.text(min_size=1), min_size=2, max_size=5))
def test_css_cannot_be_added_to_url_or_list_sources(urls):
    """Test that CSS prepending raises error for URL or list sources"""
    pdf_url = PDFKit('http://example.com', 'url', css='test.css')
    try:
        list(pdf_url._command())
        assert False, "Should raise ImproperSourceError for URL source with CSS"
    except PDFKit.ImproperSourceError as e:
        assert 'CSS files can be added only to a single file or string' in str(e)
    
    pdf_list = PDFKit(urls, 'file', css='test.css')
    try:
        list(pdf_list._command())
        assert False, "Should raise ImproperSourceError for list source with CSS"  
    except PDFKit.ImproperSourceError as e:
        assert 'CSS files can be added only to a single file or string' in str(e)


@given(st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=1, max_size=20))
def test_meta_tag_extraction_with_prefix(prefix):
    """Test that meta tag extraction only extracts tags with the configured prefix"""
    html_content = f'''
    <html>
    <head>
        <meta name="{prefix}option1" content="value1">
        <meta name="other-option" content="value2">
        <meta name='{prefix}option2' content='value3'>
    </head>
    </html>
    '''
    
    config = Configuration(meta_tag_prefix=prefix)
    pdf = PDFKit(html_content, 'string', configuration=config)
    
    found_options = pdf._find_options_in_meta(html_content)
    
    assert 'option1' in found_options
    assert found_options['option1'] == 'value1'
    assert 'option2' in found_options  
    assert found_options['option2'] == 'value3'
    assert 'other-option' not in found_options


@given(st.text())
def test_meta_tag_extraction_handles_quotes(content):
    """Test meta tag extraction handles both single and double quotes"""
    safe_content = content.replace('"', '').replace("'", '').replace('>', '').replace('<', '')[:50]
    assume(safe_content)
    
    html_double = f'<meta name="pdfkit-test" content="{safe_content}">'
    html_single = f"<meta name='pdfkit-test' content='{safe_content}'>"
    
    pdf = PDFKit('dummy', 'string')
    
    found_double = pdf._find_options_in_meta(html_double)
    found_single = pdf._find_options_in_meta(html_single)
    
    assert found_double.get('test') == safe_content
    assert found_single.get('test') == safe_content


@given(
    st.one_of(
        st.just('url'),
        st.just('file'),
        st.just('string')
    ),
    st.booleans(),
    st.dictionaries(st.text(min_size=1), st.text(), max_size=5)
)
def test_command_always_includes_wkhtmltopdf(source_type, verbose, options):
    """Test that command generation always includes wkhtmltopdf binary"""
    if source_type == 'url':
        source = 'http://example.com'
    elif source_type == 'file':
        source = 'test.html'
    else:
        source = '<html></html>'
    
    config = Configuration(wkhtmltopdf='/usr/bin/wkhtmltopdf')
    pdf = PDFKit(source, source_type, options=options, configuration=config, verbose=verbose)
    
    command = pdf.command()
    assert command[0] == '/usr/bin/wkhtmltopdf'
    
    if not verbose:
        assert '--quiet' in command


@given(st.text())
def test_source_to_s_always_returns_unicode(text):
    """Test that Source.to_s() always returns unicode/str type"""
    source = Source(text, 'string')
    result = source.to_s()
    assert isinstance(result, str)


@given(
    st.text(min_size=1),
    st.sampled_from(['</head>', '</HEAD>', '</Head>'])
)
def test_css_prepending_preserves_head_tag(html_without_style, head_tag):
    """Test that CSS prepending correctly inserts before head closing tag"""
    html_content = f'<html><head><title>Test</title>{head_tag}<body>Content</body></html>'
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.css', delete=False) as css_file:
        css_file.write('body { color: red; }')
        css_file_path = css_file.name
    
    try:
        pdf = PDFKit(html_content, 'string', css=css_file_path)
        pdf._prepend_css(css_file_path)
        
        modified_source = pdf.source.to_s()
        
        assert '<style>body { color: red; }</style>' in modified_source
        assert modified_source.count(head_tag) == 1
        
        style_index = modified_source.index('<style>')
        head_index = modified_source.lower().index('</head>')
        assert style_index < head_index
    finally:
        os.unlink(css_file_path)


@given(st.text(min_size=1))
def test_css_prepending_adds_style_when_no_head(content):
    """Test that CSS prepending adds style tag when no head tag exists"""
    assume('</head>' not in content.lower())
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.css', delete=False) as css_file:
        css_file.write('p { margin: 0; }')
        css_file_path = css_file.name
    
    try:
        pdf = PDFKit(content, 'string', css=css_file_path)
        pdf._prepend_css(css_file_path)
        
        modified_source = pdf.source.to_s()
        assert '<style>p { margin: 0; }</style>' in modified_source
        assert modified_source.startswith('<style>') or '<style>' in modified_source
    finally:
        os.unlink(css_file_path)