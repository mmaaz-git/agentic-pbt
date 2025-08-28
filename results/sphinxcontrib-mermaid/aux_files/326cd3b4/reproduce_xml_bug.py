"""Minimal reproduction for XML control character bug in sphinxcontrib.devhelp"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sphinxcontrib-mermaid_env/lib/python3.13/site-packages')

import xml.etree.ElementTree as etree
import gzip
import tempfile
import os

# Simulate what happens in build_devhelp when there are control characters
def test_control_characters_in_xml():
    """Test what happens when control characters appear in XML attributes."""
    
    # Test various control characters that might appear in titles
    test_titles = [
        "Normal Title",  # Control case
        "Title\x08Backspace",  # Backspace character
        "Title\x00Null",  # Null character  
        "Title\x01SOH",  # Start of heading
        "Title\x0BVerticalTab",  # Vertical tab
        "Title\x0CFormFeed",  # Form feed
        "Title\x0EShiftOut",  # Shift out
        "Title\x1FUnitSeparator",  # Unit separator
    ]
    
    for title in test_titles:
        print(f"\nTesting title: {repr(title)}")
        
        try:
            # Create XML element as done in build_devhelp
            root = etree.Element('book',
                                title=title,
                                name="TestProject",
                                link="index.html",
                                version="1.0")
            
            # Add a function element as done in write_index
            functions = etree.SubElement(root, 'functions')
            etree.SubElement(functions, 'function', name=title, link='test.html')
            
            # Try to serialize to XML
            tree = etree.ElementTree(root)
            
            # Write to a temporary file with gzip as done in build_devhelp
            with tempfile.NamedTemporaryFile(suffix='.devhelp.gz', delete=False) as f:
                temp_file = f.name
                
            with gzip.GzipFile(filename=temp_file, mode='w', mtime=0) as gz:
                tree.write(gz, 'utf-8')
            
            # Try to read it back and parse
            with gzip.open(temp_file, 'rt', encoding='utf-8') as gz:
                content = gz.read()
                
            # Parse the XML to verify it's valid
            parsed = etree.fromstring(content)
            
            print(f"  ✓ Success: XML is valid")
            print(f"    Title in XML: {repr(parsed.get('title'))}")
            
        except etree.ParseError as e:
            print(f"  ✗ ParseError: {e}")
            print(f"    This would cause the generated devhelp file to be invalid!")
            
        except Exception as e:
            print(f"  ✗ Unexpected error: {e}")
            
        finally:
            # Clean up temp file
            if 'temp_file' in locals() and os.path.exists(temp_file):
                os.unlink(temp_file)


if __name__ == "__main__":
    test_control_characters_in_xml()