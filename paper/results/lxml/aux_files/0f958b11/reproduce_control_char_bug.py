"""Minimal reproduction of control character handling inconsistency in lxml.html"""

import lxml.html


def demonstrate_bug():
    """Show the inconsistent handling of control characters"""
    
    # These control characters should behave consistently, but don't
    null_byte = '\x00'  # NULL
    esc_char = '\x1b'   # ESC
    
    print("Inconsistent Control Character Handling in lxml.html")
    print("=" * 55)
    
    print("\n1. Both characters parse successfully when given as raw text:")
    for name, char in [("NULL (0x00)", null_byte), ("ESC (0x1B)", esc_char)]:
        result = lxml.html.fromstring(char)
        print(f"   {name}: fromstring() -> <{result.tag}> element")
    
    print("\n2. But fragment_fromstring with create_parent=True behaves differently:")
    
    # NULL byte succeeds (inconsistent!)
    try:
        result = lxml.html.fragment_fromstring(null_byte, create_parent=True)
        print(f"   NULL (0x00): SUCCESS - creates <{result.tag}> with text={result.text!r}")
    except ValueError as e:
        print(f"   NULL (0x00): FAILS - {e}")
    
    # ESC character fails
    try:
        result = lxml.html.fragment_fromstring(esc_char, create_parent=True)
        print(f"   ESC (0x1B): SUCCESS - creates <{result.tag}> with text={result.text!r}")
    except ValueError as e:
        print(f"   ESC (0x1B): FAILS - {e}")
    
    print("\n3. The root cause - different code paths:")
    print("   When fragment_fromstring creates a parent element, it assigns")
    print("   the text using Element.text setter, which validates XML compatibility.")
    print("   But NULL byte (0x00) gets replaced with U+FFFD during parsing,")
    print("   so the validation doesn't catch it!")
    
    print("\n4. This creates an inconsistency where:")
    print("   - Most control chars (0x01-0x08, 0x0E-0x1B) fail with ValueError")
    print("   - NULL byte (0x00) silently gets replaced with U+FFFD")
    print("   - Some control chars (0x0B, 0x0C, 0x1C-0x1F) parse as whitespace")


if __name__ == "__main__":
    demonstrate_bug()