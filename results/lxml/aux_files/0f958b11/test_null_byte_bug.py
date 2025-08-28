"""Test NULL byte handling inconsistency in lxml.html"""

import lxml.html


def test_null_byte_inconsistency():
    """Demonstrate the NULL byte handling inconsistency"""
    
    # NULL byte as plain text
    null_text = '\x00'
    
    print("Test 1: fromstring with NULL byte")
    try:
        result1 = lxml.html.fromstring(null_text)
        print(f"  Success: creates <{result1.tag}> element")
        print(f"  Element text: {result1.text!r}")
        serialized = lxml.html.tostring(result1, encoding='unicode')
        print(f"  Serialized: {serialized!r}")
        
        # Check if NULL byte is preserved
        if '\x00' in serialized:
            print(f"  NULL byte preserved in output: YES")
        else:
            print(f"  NULL byte preserved in output: NO (replaced with {result1.text!r})")
    except Exception as e:
        print(f"  Error: {e}")
    
    print("\nTest 2: fragment_fromstring with NULL byte and create_parent=True")
    try:
        result2 = lxml.html.fragment_fromstring(null_text, create_parent=True)
        print(f"  Success: creates <{result2.tag}> element")
        print(f"  Element text: {result2.text!r}")
        serialized = lxml.html.tostring(result2, encoding='unicode')
        print(f"  Serialized: {serialized!r}")
    except Exception as e:
        print(f"  Expected error: {e}")
    
    print("\nTest 3: NULL byte in HTML content")
    html_with_null = '<div>before\x00after</div>'
    try:
        result3 = lxml.html.fromstring(html_with_null)
        print(f"  Success: creates <{result3.tag}> element")
        print(f"  Element text: {result3.text!r}")
        serialized = lxml.html.tostring(result3, encoding='unicode')
        print(f"  Serialized: {serialized!r}")
        
        # Check preservation
        if '\x00' in serialized:
            print(f"  NULL byte preserved: YES")
        elif '�' in serialized:
            print(f"  NULL byte replaced with: � (U+FFFD)")
        else:
            print(f"  NULL byte handling: removed or other replacement")
    except Exception as e:
        print(f"  Error: {e}")
    
    print("\nTest 4: Direct assignment vs parsing")
    print("  Creating element and assigning text with NULL byte:")
    try:
        elem = lxml.html.Element('div')
        elem.text = '\x00'
        print(f"    Direct assignment failed as expected")
    except ValueError as e:
        print(f"    Expected error: {e}")
    
    print("\n  But parsing the same content succeeds:")
    parsed = lxml.html.fromstring('\x00')
    print(f"    Parsed successfully: <{parsed.tag}> with text {parsed.text!r}")


if __name__ == "__main__":
    test_null_byte_inconsistency()