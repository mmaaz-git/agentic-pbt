"""Test carriage return normalization in lxml.html"""

import lxml.html


def test_cr_normalization():
    """Test that carriage returns are normalized to newlines"""
    
    test_cases = [
        ('Plain CR', 'text\rhere', 'text\nhere'),
        ('CR-LF', 'text\r\nhere', 'text\nhere'),
        ('Multiple CRs', 'a\r\rb', 'a\n\nb'),
        ('Mixed', 'a\rb\nc\r\nd', 'a\nb\nc\nd'),
    ]
    
    print("Carriage Return Normalization in lxml.html")
    print("=" * 45)
    
    for name, input_text, expected in test_cases:
        html = f'<div>{input_text}</div>'
        parsed = lxml.html.fromstring(html)
        
        print(f"\n{name}:")
        print(f"  Input:    {input_text!r}")
        print(f"  Parsed:   {parsed.text!r}")
        print(f"  Expected: {expected!r}")
        print(f"  Match:    {parsed.text == expected}")
        
        # Also check serialization
        serialized = lxml.html.tostring(parsed, encoding='unicode')
        print(f"  Serialized contains \\r: {'\\r' in serialized}")
        print(f"  Serialized contains \\n: {'\\n' in serialized}")
    
    print("\n" + "=" * 45)
    print("This is expected XML behavior - CR characters are normalized")
    print("to LF during parsing according to XML specification.")
    print("Not a bug, but a property to be aware of in roundtrip tests.")


if __name__ == "__main__":
    test_cr_normalization()