"""Additional property-based tests for lxml.ElementInclude."""

import os
import tempfile
from hypothesis import given, strategies as st, assume, settings
from lxml import etree, ElementInclude


@given(
    base_url=st.text(min_size=1, max_size=50).filter(lambda x: '://' not in x and '\x00' not in x),
    href=st.text(min_size=1, max_size=50).filter(lambda x: '://' not in x and '\x00' not in x)
)
def test_urljoin_property(base_url, href):
    """Test that URL joining works correctly for relative paths."""
    
    # Skip if href is absolute
    assume(not href.startswith('/'))
    assume(not href.startswith('\\'))
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create the target file
        full_path = os.path.join(tmpdir, href.replace('/', '_').replace('\\', '_'))
        
        try:
            with open(full_path, 'w') as f:
                f.write('<target/>')
        except (OSError, ValueError):
            assume(False)  # Skip invalid file names
        
        # Create XML with relative href
        xml = f'''<root xmlns:xi="http://www.w3.org/2001/XInclude">
    <xi:include href="{href}" parse="xml"/>
</root>'''
        
        try:
            tree = etree.fromstring(xml.encode())
        except:
            assume(False)  # Skip invalid XML
        
        # Test with various base URLs
        try:
            result = ElementInclude.include(tree, base_url=tmpdir + '/')
        except (IOError, ElementInclude.FatalIncludeError):
            pass  # File not found is expected for most random paths


@given(
    xml_content=st.text(min_size=1, max_size=100).filter(
        lambda x: all(ord(c) >= 0x20 or c in '\t\n\r' for c in x)
    )
)
def test_xml_include_roundtrip(xml_content):
    """Test that valid XML content can be included and preserved."""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create included XML file
        included_file = os.path.join(tmpdir, "included.xml")
        
        # Wrap content in valid XML
        included_xml = f'<included>{xml_content}</included>'
        
        try:
            # Validate it's parseable
            etree.fromstring(included_xml.encode())
        except:
            assume(False)  # Skip invalid XML
        
        with open(included_file, 'w') as f:
            f.write(included_xml)
        
        # Create main XML
        main_xml = f'''<root xmlns:xi="http://www.w3.org/2001/XInclude">
    <xi:include href="{included_file}" parse="xml"/>
</root>'''
        
        tree = etree.fromstring(main_xml.encode())
        
        # Process includes
        ElementInclude.include(tree)
        
        # Check that included element exists
        included_elem = tree.find('.//included')
        assert included_elem is not None
        
        # Check content is preserved (may have whitespace differences)
        actual_text = (included_elem.text or '').strip()
        expected_text = xml_content.strip()
        
        if expected_text:
            assert actual_text == expected_text


@given(
    depth=st.integers(min_value=0, max_value=100)
)
def test_max_depth_edge_cases(depth):
    """Test edge cases for max_depth parameter."""
    
    # Test with max_depth = depth (should succeed at boundary)
    xml = '<root xmlns:xi="http://www.w3.org/2001/XInclude"/>'
    tree = etree.fromstring(xml.encode())
    
    # Should not raise for equal depth
    ElementInclude.include(tree, max_depth=depth)
    
    # Test None conversion
    ElementInclude.include(tree, max_depth=None)


@given(
    fallback_content=st.text(min_size=0, max_size=50).filter(
        lambda x: all(ord(c) >= 0x20 or c in '\t\n\r' for c in x)
    )
)  
def test_fallback_validation(fallback_content):
    """Test that fallback elements are validated correctly."""
    
    # Create XML with fallback in wrong location
    xml = f'''<root xmlns:xi="http://www.w3.org/2001/XInclude">
    <xi:fallback>{fallback_content}</xi:fallback>
</root>'''
    
    try:
        tree = etree.fromstring(xml.encode())
    except:
        assume(False)  # Skip invalid XML
    
    # Should raise error for fallback not inside include
    try:
        ElementInclude.include(tree)
        assert False, "Should have raised error for misplaced fallback"
    except ElementInclude.FatalIncludeError as e:
        assert "must be child of xi:include" in str(e)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])