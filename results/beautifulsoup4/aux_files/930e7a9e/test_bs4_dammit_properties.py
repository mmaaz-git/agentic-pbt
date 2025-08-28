"""Property-based tests for bs4.dammit module using Hypothesis."""

import codecs
import re
from hypothesis import given, strategies as st, assume, settings
import bs4.dammit


# Strategy for generating text that might contain special XML/HTML characters
xml_text = st.text(alphabet=st.characters(codec='utf-8'), min_size=0, max_size=100)
ascii_text = st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), min_size=0, max_size=100)

# Strategy for valid encoding names
encoding_names = st.sampled_from([
    'utf-8', 'utf-16', 'utf-32', 'ascii', 'iso-8859-1', 'windows-1252',
    'cp1252', 'latin-1', 'UTF-8', 'UTF8', 'utf_8', 'U8', 'UTF',
    'cp1251', 'koi8-r', 'gb2312', 'shift_jis', 'euc-jp', 'big5'
])


@given(xml_text)
def test_substitute_xml_escapes_special_chars(text):
    """Test that substitute_xml correctly escapes <, >, and & as documented."""
    result = bs4.dammit.EntitySubstitution.substitute_xml(text)
    
    # The docstring says: "The less-than sign will become &lt;, the greater-than sign
    # will become &gt;, and any ampersands will become &amp;"
    
    # Check that no unescaped < or > remain
    # We need to be careful about & - only raw & should be escaped, not those in entities
    assert '<' not in result or '&lt;' in result
    assert '>' not in result or '&gt;' in result
    
    # Count original characters and their replacements
    original_lt_count = text.count('<')
    original_gt_count = text.count('>')
    result_lt_entity_count = result.count('&lt;')
    result_gt_entity_count = result.count('&gt;')
    
    # Every < should become &lt;
    assert result_lt_entity_count == original_lt_count
    # Every > should become &gt;
    assert result_gt_entity_count == original_gt_count


@given(xml_text)
def test_substitute_xml_containing_entities_handles_existing_entities(text):
    """Test that substitute_xml_containing_entities handles text that may already contain entities."""
    result = bs4.dammit.EntitySubstitution.substitute_xml_containing_entities(text)
    
    # According to the docstring, this version is smart about not double-escaping
    # ampersands that appear to be part of entities
    
    # The result should still not contain unescaped < or >
    assert '<' not in result or '&lt;' in result
    assert '>' not in result or '&gt;' in result


@given(xml_text)
def test_quoted_attribute_value_produces_quoted_output(text):
    """Test that quoted_attribute_value always produces a quoted string."""
    result = bs4.dammit.EntitySubstitution.quoted_attribute_value(text)
    
    # The docstring says it returns a quoted XML attribute
    # It should start and end with quotes (either single or double)
    assert (result.startswith('"') and result.endswith('"')) or \
           (result.startswith("'") and result.endswith("'"))
    
    # The content between quotes should be properly escaped
    # If we used double quotes and the text contains double quotes,
    # they should be escaped inside
    if result.startswith('"') and result.endswith('"'):
        inner = result[1:-1]
        # Check that any quotes inside are escaped
        if '"' in text:
            # The function should either escape internal quotes or use single quotes
            assert ('&quot;' in inner) or (result.startswith("'") and result.endswith("'"))


@given(st.binary(min_size=1, max_size=1000))
def test_unicode_dammit_preserves_valid_utf8(data):
    """Test that UnicodeDammit correctly decodes valid UTF-8 data."""
    # Try to decode as UTF-8 to check if it's valid
    try:
        expected = data.decode('utf-8')
    except UnicodeDecodeError:
        # Not valid UTF-8, skip this test case
        assume(False)
    
    # UnicodeDammit should correctly decode valid UTF-8
    ud = bs4.dammit.UnicodeDammit(data)
    assert ud.unicode_markup == expected
    assert ud.original_encoding in ['utf-8', 'ascii']  # ASCII is a subset of UTF-8


@given(st.binary(min_size=1, max_size=1000))
def test_unicode_dammit_detected_encoding_can_decode(data):
    """Test that the encoding detected by UnicodeDammit can actually decode the data."""
    ud = bs4.dammit.UnicodeDammit(data)
    
    if ud.original_encoding:
        # The detected encoding should be able to decode the original data
        # without raising an exception
        try:
            # Try to decode with the detected encoding
            decoded = data.decode(ud.original_encoding, errors='strict')
            # The unicode_markup should match what we get from direct decoding
            # (allowing for some normalization)
            assert ud.unicode_markup is not None
        except (UnicodeDecodeError, LookupError) as e:
            # If we can't decode with the reported encoding, that's a bug
            assert False, f"Detected encoding {ud.original_encoding} cannot decode the data: {e}"


@given(encoding_names)
def test_find_codec_returns_valid_python_codec(encoding_name):
    """Test that find_codec returns valid Python codec names."""
    # Create a dummy UnicodeDammit instance to test find_codec
    ud = bs4.dammit.UnicodeDammit(b'test')
    
    result = ud.find_codec(encoding_name)
    
    if result is not None:
        # If find_codec returns a codec name, it should be valid for Python's codecs
        try:
            codec = codecs.lookup(result)
            assert codec is not None
        except LookupError:
            assert False, f"find_codec returned '{result}' which is not a valid Python codec"


@given(xml_text)
def test_substitute_html_vs_html5_ampersand_handling(text):
    """Test difference in ampersand handling between substitute_html and substitute_html5."""
    html_result = bs4.dammit.EntitySubstitution.substitute_html(text)
    html5_result = bs4.dammit.EntitySubstitution.substitute_html5(text)
    
    # According to docstring, substitute_html5 is less aggressive about escaping ampersands
    # Both should escape < and >
    for result in [html_result, html5_result]:
        assert '<' not in result or '&lt;' in result
        assert '>' not in result or '&gt;' in result
    
    # If the text contains ampersands, html5 might have fewer &amp; entities
    if '&' in text:
        # HTML5 should be less aggressive (fewer or equal replacements)
        assert html5_result.count('&amp;') <= html_result.count('&amp;')


@given(st.binary(min_size=0, max_size=100))
def test_unicode_dammit_always_produces_unicode(data):
    """Test that UnicodeDammit always produces unicode output."""
    ud = bs4.dammit.UnicodeDammit(data)
    
    # unicode_markup should always be a string (unicode), never bytes
    assert isinstance(ud.unicode_markup, str)
    
    # The output should not contain replacement characters unless necessary
    if not ud.contains_replacement_characters:
        assert '\ufffd' not in ud.unicode_markup


@given(ascii_text)
def test_entity_substitution_reversibility(text):
    """Test that we can detect when text has been entity-substituted."""
    # Escape the text
    escaped = bs4.dammit.EntitySubstitution.substitute_xml(text)
    
    # If we had special characters, they should now be entities
    if '<' in text:
        assert '&lt;' in escaped
    if '>' in text:
        assert '&gt;' in escaped
    if '&' in text:
        assert '&amp;' in escaped
    
    # The escaped version should have more or equal length (entities are longer)
    assert len(escaped) >= len(text)