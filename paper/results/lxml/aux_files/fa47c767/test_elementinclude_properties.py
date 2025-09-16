"""Property-based tests for lxml.ElementInclude module."""

import os
import tempfile
from hypothesis import given, strategies as st, assume, settings
from lxml import etree, ElementInclude
import math


@given(
    max_depth=st.integers(min_value=0, max_value=10),
    actual_depth=st.integers(min_value=0, max_value=15)
)
def test_max_depth_limit_property(max_depth, actual_depth):
    """Test that max_depth limit is properly enforced for recursive includes."""
    
    # Create a chain of XML files that include each other
    with tempfile.TemporaryDirectory() as tmpdir:
        files = []
        
        # Create a chain of includes
        for i in range(actual_depth + 1):
            filename = os.path.join(tmpdir, f"file_{i}.xml")
            files.append(filename)
            
            if i < actual_depth:
                # This file includes the next one
                content = f'''<?xml version="1.0"?>
<level{i} xmlns:xi="http://www.w3.org/2001/XInclude">
    <data>Level {i}</data>
    <xi:include href="file_{i+1}.xml" parse="xml"/>
</level{i}>'''
            else:
                # Last file doesn't include anything
                content = f'''<?xml version="1.0"?>
<level{i}>
    <data>Level {i}</data>
</level{i}>'''
            
            with open(filename, 'w') as f:
                f.write(content)
        
        # Try to process the first file with given max_depth
        tree = etree.parse(files[0])
        
        if actual_depth > max_depth:
            # Should raise LimitedRecursiveIncludeError
            try:
                ElementInclude.include(tree, max_depth=max_depth)
                assert False, f"Should have raised error for depth {actual_depth} > max {max_depth}"
            except ElementInclude.LimitedRecursiveIncludeError:
                pass  # Expected
        else:
            # Should succeed
            ElementInclude.include(tree, max_depth=max_depth)
            # Verify all levels were included
            result = etree.tostring(tree.getroot(), pretty_print=True).decode()
            for i in range(min(actual_depth + 1, max_depth + 1)):
                assert f"Level {i}" in result


@given(
    text_content=st.text(min_size=0, max_size=100),
    encoding=st.sampled_from(['utf-8', 'latin-1', 'ascii'])
)
def test_text_include_preserves_content(text_content, encoding):
    """Test that text includes preserve the exact content."""
    
    # Skip if text isn't encodable with chosen encoding
    try:
        encoded = text_content.encode(encoding)
    except UnicodeEncodeError:
        assume(False)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create text file
        text_file = os.path.join(tmpdir, "text.txt")
        with open(text_file, 'wb') as f:
            f.write(encoded)
        
        # Create XML that includes the text
        xml_file = os.path.join(tmpdir, "main.xml")
        xml_content = f'''<?xml version="1.0"?>
<root xmlns:xi="http://www.w3.org/2001/XInclude">
    <before>Before</before>
    <xi:include href="text.txt" parse="text" encoding="{encoding}"/>
    <after>After</after>
</root>'''
        
        with open(xml_file, 'w') as f:
            f.write(xml_content)
        
        # Process includes
        tree = etree.parse(xml_file)
        ElementInclude.include(tree)
        
        # Extract text content
        root = tree.getroot()
        all_text = ''.join(root.itertext())
        
        # Property: included text should be preserved exactly
        assert text_content in all_text
        assert all_text == f"Before{text_content}After"


@given(
    parse_mode=st.text(min_size=1, max_size=20)
)
def test_invalid_parse_mode_raises_error(parse_mode):
    """Test that invalid parse modes raise appropriate errors."""
    
    # Skip valid parse modes
    assume(parse_mode not in ['xml', 'text'])
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create dummy file
        dummy_file = os.path.join(tmpdir, "dummy.txt")
        with open(dummy_file, 'w') as f:
            f.write("dummy content")
        
        # Create XML with invalid parse mode
        xml_content = f'''<?xml version="1.0"?>
<root xmlns:xi="http://www.w3.org/2001/XInclude">
    <xi:include href="dummy.txt" parse="{parse_mode}"/>
</root>'''
        
        tree = etree.fromstring(xml_content.encode())
        
        # Should raise FatalIncludeError for unknown parse type
        try:
            ElementInclude.include(tree, base_url=tmpdir + '/')
            assert False, f"Should have raised error for parse mode '{parse_mode}'"
        except ElementInclude.FatalIncludeError as e:
            assert "unknown parse type" in str(e)


@given(
    empty_href=st.just("")
)
def test_empty_href_handling(empty_href):
    """Test how empty href attribute is handled."""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create XML with empty href
        xml_content = f'''<?xml version="1.0"?>
<root xmlns:xi="http://www.w3.org/2001/XInclude">
    <xi:include href="{empty_href}" parse="xml"/>
</root>'''
        
        tree = etree.fromstring(xml_content.encode())
        
        # Test with base_url to avoid file not found issues
        base_file = os.path.join(tmpdir, "base.xml")
        with open(base_file, 'w') as f:
            f.write('<empty/>')
        
        try:
            ElementInclude.include(tree, base_url=base_file)
            # If it succeeds, it should have loaded the base file itself
            result = etree.tostring(tree, pretty_print=True).decode()
            assert 'empty' in result
        except (IOError, ElementInclude.FatalIncludeError):
            # This is also acceptable behavior
            pass


@given(
    negative_depth=st.integers(max_value=-1)
)
def test_negative_max_depth_validation(negative_depth):
    """Test that negative max_depth values are properly validated."""
    
    # Skip -1 which is handled specially
    assume(negative_depth != -1)
    
    xml_content = '''<?xml version="1.0"?>
<root xmlns:xi="http://www.w3.org/2001/XInclude">
    <data>Test</data>
</root>'''
    
    tree = etree.fromstring(xml_content.encode())
    
    # Should raise ValueError for negative max_depth (except -1)
    try:
        ElementInclude.include(tree, max_depth=negative_depth)
        assert False, f"Should have raised ValueError for max_depth={negative_depth}"
    except ValueError as e:
        assert "expected non-negative depth" in str(e)


@given(
    tail_text=st.text(min_size=0, max_size=50),
    included_tail=st.text(min_size=0, max_size=50)
)
def test_tail_text_concatenation(tail_text, included_tail):
    """Test that tail text is properly concatenated when including XML."""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create included file with tail text
        included_file = os.path.join(tmpdir, "included.xml")
        included_content = f'''<?xml version="1.0"?>
<included>Content</included>'''
        
        with open(included_file, 'w') as f:
            f.write(included_content)
        
        # Create main file with xi:include that has tail text
        xml_content = f'''<?xml version="1.0"?>
<root xmlns:xi="http://www.w3.org/2001/XInclude">
    <before/>
    <xi:include href="included.xml" parse="xml"/>{tail_text}
    <after/>
</root>'''
        
        tree = etree.fromstring(xml_content.encode())
        
        # Manually set tail on included element for testing
        included = etree.fromstring(included_content.encode())
        included.tail = included_tail
        
        # Custom loader that adds tail
        def custom_loader(href, parse, encoding=None):
            if parse == "xml":
                result = etree.fromstring(included_content.encode())
                result.tail = included_tail
                return result
            return None
        
        # Process includes
        ElementInclude.include(tree, loader=custom_loader, base_url=tmpdir + '/')
        
        # The tail from xi:include should be appended to included element's tail
        root = tree.getroot()
        included_elem = root[1]  # The included element
        
        if included_tail and tail_text:
            assert included_elem.tail == included_tail + tail_text
        elif tail_text:
            assert included_elem.tail == tail_text
        elif included_tail:
            assert included_elem.tail == included_tail


@given(
    href=st.text(min_size=1, max_size=100).filter(lambda x: '://' not in x and not x.startswith('/'))
)
def test_relative_href_resolution(href):
    """Test that relative hrefs are resolved correctly with base_url."""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create subdirectory structure
        subdir = os.path.join(tmpdir, "subdir")
        os.makedirs(subdir, exist_ok=True)
        
        # Create target file
        target_file = os.path.join(subdir, "target.xml")
        with open(target_file, 'w') as f:
            f.write('<?xml version="1.0"?><target/>')
        
        # Create XML with relative href
        xml_content = f'''<?xml version="1.0"?>
<root xmlns:xi="http://www.w3.org/2001/XInclude">
    <xi:include href="subdir/target.xml" parse="xml"/>
</root>'''
        
        tree = etree.fromstring(xml_content.encode())
        
        # Process with base_url
        ElementInclude.include(tree, base_url=tmpdir + '/')
        
        # Should have successfully included the target
        result = etree.tostring(tree, pretty_print=True).decode()
        assert '<target/>' in result


@given(
    use_none_max_depth=st.booleans()
)
def test_none_max_depth_allows_unlimited(use_none_max_depth):
    """Test that max_depth=None allows unlimited recursion depth."""
    
    depth = 10  # Test with a reasonable depth
    
    with tempfile.TemporaryDirectory() as tmpdir:
        files = []
        
        # Create a chain of includes
        for i in range(depth):
            filename = os.path.join(tmpdir, f"file_{i}.xml")
            files.append(filename)
            
            if i < depth - 1:
                content = f'''<?xml version="1.0"?>
<level{i} xmlns:xi="http://www.w3.org/2001/XInclude">
    <xi:include href="file_{i+1}.xml" parse="xml"/>
</level{i}>'''
            else:
                content = f'''<?xml version="1.0"?>
<level{i}/>'''
            
            with open(filename, 'w') as f:
                f.write(content)
        
        tree = etree.parse(files[0])
        
        if use_none_max_depth:
            # Should succeed with unlimited depth
            ElementInclude.include(tree, max_depth=None)
            result = etree.tostring(tree.getroot(), pretty_print=True).decode()
            for i in range(depth):
                assert f"level{i}" in result.lower()
        else:
            # Default max_depth should limit
            if depth > ElementInclude.DEFAULT_MAX_INCLUSION_DEPTH:
                try:
                    ElementInclude.include(tree)
                    assert False, "Should have hit default depth limit"
                except ElementInclude.LimitedRecursiveIncludeError:
                    pass


if __name__ == "__main__":
    # Run all tests
    import pytest
    pytest.main([__file__, "-v"])