import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pdfkit_env/lib/python3.13/site-packages')

import io
import os
import tempfile
from hypothesis import given, strategies as st, assume, settings
from hypothesis import example
import pdfkit
from pdfkit.pdfkit import PDFKit
from pdfkit.source import Source
from pdfkit.configuration import Configuration

# Mock configuration to avoid wkhtmltopdf dependency
class MockConfiguration:
    def __init__(self, wkhtmltopdf='/fake/wkhtmltopdf', meta_tag_prefix='pdfkit-', environ=None):
        self.wkhtmltopdf = wkhtmltopdf
        self.meta_tag_prefix = meta_tag_prefix
        self.environ = environ if environ is not None else os.environ

# Test 1: _normalize_arg always returns lowercase
@given(st.text(min_size=1))
def test_normalize_arg_lowercase(arg):
    pdf = PDFKit('test', 'string', configuration=MockConfiguration())
    result = pdf._normalize_arg(arg)
    assert result == arg.lower()

# Test 2: _normalize_options idempotence - normalizing twice gives same result
@given(st.dictionaries(
    st.text(min_size=1),
    st.one_of(
        st.text(),
        st.booleans(),
        st.lists(st.text(), min_size=1, max_size=5)
    ),
    min_size=1,
    max_size=10
))
def test_normalize_options_idempotence(options):
    pdf = PDFKit('test', 'string', configuration=MockConfiguration())
    
    # First normalization
    normalized_once = list(pdf._normalize_options(options))
    
    # Convert back to dict for second normalization
    options_dict = {}
    for key, val in normalized_once:
        if key not in options_dict:
            options_dict[key] = []
        options_dict[key].append(val)
    
    # For single values, unwrap from list
    for key in options_dict:
        if len(options_dict[key]) == 1:
            options_dict[key] = options_dict[key][0]
    
    # Second normalization
    normalized_twice = list(pdf._normalize_options(options_dict))
    
    # Should be same
    assert normalized_once == normalized_twice

# Test 3: Meta tag parsing correctly extracts options
@given(
    st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=1, max_size=20),  # option name
    st.text(min_size=1, max_size=100).filter(lambda x: '"' not in x and "'" not in x),  # option value
    st.sampled_from(['pdfkit-', 'custom-', 'test-'])  # prefix
)
def test_meta_tag_parsing(option_name, option_value, prefix):
    config = MockConfiguration(meta_tag_prefix=prefix)
    pdf = PDFKit('test', 'string', configuration=config)
    
    # Create HTML with meta tag
    html = f'<html><head><meta name="{prefix}{option_name}" content="{option_value}"></head><body></body></html>'
    
    # Parse options
    found_options = pdf._find_options_in_meta(html)
    
    # Check if option was found correctly
    assert option_name in found_options
    assert found_options[option_name] == option_value

# Test 4: Source type detection
@given(st.sampled_from(['url', 'file', 'string']))
def test_source_type_detection(type_):
    if type_ == 'url':
        source = Source('http://example.com', 'url')
        assert source.isUrl()
        assert not source.isFile()
        assert not source.isString()
    elif type_ == 'file':
        # Create a temporary file for testing
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b'test')
            tmp_path = tmp.name
        try:
            source = Source(tmp_path, 'file')
            assert source.isFile()
            assert not source.isUrl()
            assert not source.isString()
        finally:
            os.unlink(tmp_path)
    else:  # string
        source = Source('test content', 'string')
        assert source.isString()
        assert not source.isUrl()
        assert not source.isFile()

# Test 5: CSS prepending preserves HTML structure
@given(
    st.text(min_size=1, max_size=100).filter(lambda x: '\n' not in x),  # css content
    st.text(min_size=1, max_size=100).filter(lambda x: '</head>' not in x.lower())  # body content
)
def test_css_prepending_preserves_structure(css_content, body_content):
    # Create test HTML
    original_html = f'<html><head><title>Test</title></head><body>{body_content}</body></html>'
    
    # Create PDFKit instance with string source
    pdf = PDFKit(original_html, 'string', configuration=MockConfiguration())
    
    # Create a temporary CSS file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.css', delete=False, encoding='utf-8') as css_file:
        css_file.write(css_content)
        css_path = css_file.name
    
    try:
        # Prepend CSS
        pdf._prepend_css(css_path)
        
        # Check that the CSS was added
        modified_html = pdf.source.to_s()
        assert '<style>' in modified_html
        assert css_content in modified_html
        assert '</head>' in modified_html
        assert body_content in modified_html
        
        # CSS should be inserted before </head>
        style_index = modified_html.index('<style>')
        head_close_index = modified_html.index('</head>')
        assert style_index < head_close_index
        
    finally:
        os.unlink(css_path)

# Test 6: _genargs handles empty values correctly
@given(st.dictionaries(
    st.text(min_size=1, max_size=20),
    st.one_of(
        st.text(min_size=0),  # Can be empty
        st.booleans(),
        st.none(),
        st.lists(st.text(), min_size=2, max_size=2)  # Tuple-like list
    )
))
def test_genargs_handles_values(options):
    pdf = PDFKit('test', 'string', options=options, configuration=MockConfiguration())
    
    # Generate args
    args = list(pdf._genargs(options))
    
    # All args should be strings or empty/None
    for arg in args:
        assert arg is None or arg == '' or isinstance(arg, str)

# Test 7: handle_error detection of 'Done' in stderr
@given(
    st.integers(min_value=1, max_value=255),  # Non-zero exit code
    st.text(min_size=1, max_size=100)  # Random stderr content
)
def test_handle_error_done_detection(exit_code, stderr_content):
    # Test that 'Done' on second-to-last line causes no error
    stderr_with_done = f"{stderr_content}\nDone\nExtra line"
    
    try:
        PDFKit.handle_error(exit_code, stderr_with_done)
        # Should not raise when 'Done' is present
        success = True
    except IOError:
        success = False
    
    # According to code, should succeed when 'Done' is on second-to-last line
    assert success

# Test 8: Source.to_s handles unicode correctly
@given(st.text())
def test_source_to_s_unicode(text):
    source = Source(text, 'string')
    result = source.to_s()
    assert isinstance(result, str)
    assert result == text