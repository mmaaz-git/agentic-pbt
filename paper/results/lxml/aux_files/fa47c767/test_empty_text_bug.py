"""Test the empty text content bug found by Hypothesis."""

import os
import tempfile
from lxml import etree, ElementInclude

def test_empty_text_include():
    """Test that empty text includes preserve document structure."""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create empty text file
        text_file = os.path.join(tmpdir, "empty.txt")
        with open(text_file, 'w') as f:
            f.write('')  # Empty file
        
        # Create XML that includes empty text
        xml_content = f'''<?xml version="1.0"?>
<root xmlns:xi="http://www.w3.org/2001/XInclude">
    <before>Before</before>
    <xi:include href="{text_file}" parse="text"/>
    <after>After</after>
</root>'''
        
        tree = etree.fromstring(xml_content.encode())
        
        print("XML before include:")
        print(etree.tostring(tree, pretty_print=True).decode())
        
        # Process includes
        ElementInclude.include(tree)
        
        print("\nXML after include:")
        print(etree.tostring(tree, pretty_print=True).decode())
        
        # Get all text
        root = tree
        all_text = ''.join(root.itertext())
        
        print(f"\nExtracted text: {repr(all_text)}")
        print(f"Expected text: {repr('BeforeAfter')}")
        
        # Check if text is preserved correctly
        if all_text.replace('\n', '').replace(' ', '') == 'BeforeAfter':
            print("✓ Structure preserved (whitespace differences acceptable)")
        else:
            print("✗ BUG: Empty text include changes document structure incorrectly")
            return False
        
        return True


def test_whitespace_text_include():
    """Test that whitespace-only text includes are handled correctly."""
    
    test_cases = [
        ('', 'empty'),
        (' ', 'single space'),
        ('  ', 'two spaces'),
        ('\n', 'newline'),
        ('\t', 'tab'),
        (' \n\t ', 'mixed whitespace'),
    ]
    
    print("\n" + "=" * 50)
    print("Testing whitespace text includes:")
    print("=" * 50)
    
    for content, description in test_cases:
        with tempfile.TemporaryDirectory() as tmpdir:
            text_file = os.path.join(tmpdir, "text.txt")
            with open(text_file, 'w') as f:
                f.write(content)
            
            xml_content = f'''<?xml version="1.0"?>
<root xmlns:xi="http://www.w3.org/2001/XInclude">
    <before>A</before>
    <xi:include href="{text_file}" parse="text"/>
    <after>B</after>
</root>'''
            
            tree = etree.fromstring(xml_content.encode())
            ElementInclude.include(tree)
            
            all_text = ''.join(tree.itertext())
            # Remove formatting whitespace from pretty printing
            actual = all_text.replace('\n    ', '').replace('\n', '')
            expected = f'A{content}B'
            
            if actual == expected:
                print(f"✓ {description:20} preserved correctly")
            else:
                print(f"✗ {description:20} failed:")
                print(f"  Expected: {repr(expected)}")
                print(f"  Actual:   {repr(actual)}")


def test_text_placement_bug():
    """Test where text gets placed when including into empty elements."""
    
    print("\n" + "=" * 50)
    print("Testing text placement with empty parent:")
    print("=" * 50)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        text_file = os.path.join(tmpdir, "content.txt")
        with open(text_file, 'w') as f:
            f.write('INCLUDED_TEXT')
        
        # Test case 1: Include as only child
        xml1 = f'''<?xml version="1.0"?>
<root xmlns:xi="http://www.w3.org/2001/XInclude">
    <xi:include href="{text_file}" parse="text"/>
</root>'''
        
        tree1 = etree.fromstring(xml1.encode())
        
        print("Case 1: Include as only child")
        print("Before:", etree.tostring(tree1, encoding='unicode'))
        
        ElementInclude.include(tree1)
        
        print("After:", etree.tostring(tree1, encoding='unicode'))
        
        if tree1.text == 'INCLUDED_TEXT':
            print("✓ Text correctly placed as parent.text")
        else:
            print(f"✗ Text placement wrong: {repr(tree1.text)}")
        
        # Test case 2: Include with no predecessor
        xml2 = f'''<?xml version="1.0"?>
<root xmlns:xi="http://www.w3.org/2001/XInclude">
    <xi:include href="{text_file}" parse="text"/>
    <after>After</after>
</root>'''
        
        tree2 = etree.fromstring(xml2.encode())
        ElementInclude.include(tree2)
        
        print("\nCase 2: Include with following sibling")
        print("Result:", etree.tostring(tree2, encoding='unicode'))
        
        # Test case 3: Include with predecessor
        xml3 = f'''<?xml version="1.0"?>
<root xmlns:xi="http://www.w3.org/2001/XInclude">
    <before>Before</before>
    <xi:include href="{text_file}" parse="text"/>
</root>'''
        
        tree3 = etree.fromstring(xml3.encode())
        ElementInclude.include(tree3)
        
        print("\nCase 3: Include with preceding sibling")
        print("Result:", etree.tostring(tree3, encoding='unicode'))
        
        before_elem = tree3.find('before')
        if before_elem.tail == 'INCLUDED_TEXT':
            print("✓ Text correctly placed as predecessor.tail")
        else:
            print(f"✗ Text placement wrong: {repr(before_elem.tail)}")


if __name__ == "__main__":
    test_empty_text_include()
    test_whitespace_text_include()
    test_text_placement_bug()