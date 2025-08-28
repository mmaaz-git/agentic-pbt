"""Property-based tests for sphinxcontrib.devhelp"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sphinxcontrib-mermaid_env/lib/python3.13/site-packages')

import re
import gzip
import xml.etree.ElementTree as etree
from hypothesis import given, strategies as st, assume
from sphinx.util.osutil import make_filename


# Test 1: make_filename should always return a non-empty valid filename
@given(st.text())
def test_make_filename_always_returns_valid_filename(s):
    """Test that make_filename always returns a non-empty string."""
    result = make_filename(s)
    
    # Property 1: Result should always be a string
    assert isinstance(result, str)
    
    # Property 2: Result should never be empty
    assert len(result) > 0
    
    # Property 3: Result should only contain allowed characters or be 'sphinx'
    if result == 'sphinx':
        # This is the fallback case
        pass
    else:
        # Should only contain alphanumeric, underscore, or hyphen
        assert re.match(r'^[a-zA-Z0-9_-]+$', result)


# Test 2: make_filename should be idempotent for valid filenames
@given(st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), whitelist_characters='_-'), min_size=1))
def test_make_filename_idempotent_for_valid_names(s):
    """Test that applying make_filename twice gives the same result for valid inputs."""
    first_result = make_filename(s)
    second_result = make_filename(first_result)
    
    # Property: Idempotence for valid filenames
    assert first_result == second_result


# Test 3: XML attribute values should be properly escaped
@given(st.text())
def test_xml_attribute_escaping(text):
    """Test that XML attributes handle all text properly without errors."""
    # Create an XML element with the text as attribute
    elem = etree.Element('test', name=text, link=text)
    
    # Should be able to serialize to XML
    xml_str = etree.tostring(elem, encoding='unicode')
    
    # Should be able to parse it back
    parsed = etree.fromstring(xml_str)
    
    # The parsed attributes should match the original (possibly with some transformations)
    # Note: null bytes get converted to spaces
    expected_text = text.replace('\x00', ' ')
    assert parsed.get('name') == expected_text
    assert parsed.get('link') == expected_text


# Test 4: Parent title extraction regex from write_index
@given(st.text())
def test_parent_title_extraction(title):
    """Test the regex used in write_index to extract parent title."""
    # This is the regex from write_index function
    parent_title = re.sub(r'\s*\(.*\)\s*$', '', title)
    
    # Property 1: Result should not have trailing parentheses with content
    assert not re.search(r'\s*\(.*\)\s*$', parent_title)
    
    # Property 2: If there are no parentheses, title should be unchanged (except trailing spaces)
    if '(' not in title and ')' not in title:
        assert parent_title == title.rstrip()
    
    # Property 3: Result should be a prefix of the original (after stripping)
    assert title.rstrip().startswith(parent_title) or parent_title == title.rstrip()


# Test 5: Test that numbered index entries are formatted correctly  
@given(st.text(), st.integers(min_value=0, max_value=1000))
def test_numbered_index_format(title, index):
    """Test the format string used for numbered index entries."""
    # This simulates the format used in write_index for multiple refs
    formatted = "[%d] %s" % (index, title)
    
    # Property: The format should always produce a valid string
    assert isinstance(formatted, str)
    assert formatted.startswith(f"[{index}] ")
    assert formatted.endswith(title)


# Test 6: Parentheses stripping handles nested parentheses
@given(st.text(alphabet=st.characters(blacklist_categories=('Cc', 'Cs'))))
def test_nested_parentheses_handling(text):
    """Test that the regex handles various parentheses patterns."""
    # Add various parentheses patterns
    test_cases = [
        text + "()",
        text + "(arg)",
        text + "(arg1, arg2)",
        text + " (spaced) ",
        text + "((nested))",
        text + "(outer(inner))",
    ]
    
    for test_title in test_cases:
        parent_title = re.sub(r'\s*\(.*\)\s*$', '', test_title)
        
        # The result should be the base text (possibly with some modifications)
        # It should not end with parentheses
        assert not parent_title.endswith(')')
        
        # For simple cases, it should equal the base text
        if test_title.startswith(text):
            assert parent_title.startswith(text.rstrip()) or parent_title == text


# Test 7: Windows reserved names are not filtered
@given(st.sampled_from(['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 
                         'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 
                         'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']))
def test_windows_reserved_names_not_filtered(reserved_name):
    """Test that Windows reserved names are NOT filtered by make_filename."""
    result = make_filename(reserved_name)
    
    # Property: Windows reserved names pass through unchanged
    assert result == reserved_name
    
    # This could be a potential issue on Windows systems
    # as these names are not valid filenames on Windows


# Test 8: Unicode handling in make_filename
@given(st.text(alphabet=st.characters(min_codepoint=128)))
def test_unicode_handling(unicode_text):
    """Test how make_filename handles non-ASCII Unicode characters."""
    assume(len(unicode_text) > 0)
    
    result = make_filename(unicode_text)
    
    # Property: Should either strip Unicode or return 'sphinx'
    assert result == 'sphinx' or re.match(r'^[a-zA-Z0-9_-]+$', result)
    
    # Most Unicode gets stripped, potentially resulting in 'sphinx'
    if not any(c in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for c in unicode_text):
        assert result == 'sphinx'


# Test 9: Format string injection in write_index
@given(st.text())
def test_format_string_safety(title):
    """Test that format strings in titles don't cause issues."""
    # Simulate the format operations from write_index
    try:
        # Test the numbered format
        formatted = "[%d] %s" % (0, title)
        assert isinstance(formatted, str)
        
        # Test the parent + child format (simulated)
        parent_title = re.sub(r'\s*\(.*\)\s*$', '', title)
        child_formatted = f'{parent_title} child'
        assert isinstance(child_formatted, str)
        
    except (TypeError, ValueError) as e:
        # Format string operations should not raise exceptions
        assert False, f"Format string operation failed with: {e}"