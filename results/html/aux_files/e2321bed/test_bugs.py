import html
from html.parser import HTMLParser


def test_control_char_bug():
    """Demonstrate bug in html.unescape with control characters"""
    
    print("Bug 1: Inconsistent control character handling in html.unescape")
    print("=" * 60)
    
    # Test control characters that should be unescaped but aren't
    control_chars = [
        (1, r'\x01'),
        (2, r'\x02'),
        (3, r'\x03'),
        (4, r'\x04'),
        (5, r'\x05'),
        (6, r'\x06'),
        (7, r'\x07'),
        (8, r'\x08'),
        (11, r'\x0b'),
        (14, r'\x0e'),
        (15, r'\x0f'),
        (16, r'\x10'),
        (17, r'\x11'),
        (18, r'\x12'),
        (19, r'\x13'),
        (20, r'\x14'),
        (21, r'\x15'),
        (22, r'\x16'),
        (23, r'\x17'),
        (24, r'\x18'),
        (25, r'\x19'),
        (26, r'\x1a'),
        (27, r'\x1b'),
        (28, r'\x1c'),
        (29, r'\x1d'),
        (30, r'\x1e'),
        (31, r'\x1f'),
    ]
    
    failures = []
    for codepoint, repr_str in control_chars:
        dec_ref = f"&#{codepoint};"
        hex_ref = f"&#x{codepoint:x};"
        
        dec_result = html.unescape(dec_ref)
        hex_result = html.unescape(hex_ref)
        expected = chr(codepoint)
        
        if dec_result != expected:
            failures.append((codepoint, dec_ref, repr(dec_result), repr(expected)))
            
    if failures:
        print(f"Found {len(failures)} failures:")
        for cp, ref, got, expected in failures[:5]:  # Show first 5
            print(f"  {ref} -> {got} (expected: {expected})")
        if len(failures) > 5:
            print(f"  ... and {len(failures) - 5} more")
    
    # Also test that hex and decimal should produce same result
    print("\nHex vs Decimal consistency:")
    for cp in [1, 8, 11, 31]:
        dec_ref = f"&#{cp};"
        hex_ref = f"&#x{cp:x};"
        dec_result = html.unescape(dec_ref)
        hex_result = html.unescape(hex_ref)
        
        if dec_result == hex_result:
            print(f"  ✓ {dec_ref} and {hex_ref} -> {repr(dec_result)}")
        else:
            print(f"  ✗ {dec_ref} -> {repr(dec_result)}, {hex_ref} -> {repr(hex_result)}")


def test_incremental_feed_bug():
    """Demonstrate bug in HTMLParser incremental feeding"""
    
    print("\n\nBug 2: HTMLParser produces different results for incremental feeding")
    print("=" * 60)
    
    class DataCollector(HTMLParser):
        def __init__(self):
            super().__init__()
            self.data = []
            
        def handle_data(self, data):
            self.data.append(data)
    
    # Test case that shows the bug
    test_strings = ['00', '11', 'aa', 'AA', '  ', '...']
    
    for text in test_strings:
        # Parse all at once
        parser1 = DataCollector()
        parser1.feed(text)
        parser1.close()
        
        # Parse incrementally (split at position 1)
        parser2 = DataCollector()
        parser2.feed(text[:1])
        parser2.feed(text[1:])
        parser2.close()
        
        if parser1.data != parser2.data:
            print(f"  ✗ '{text}': all-at-once={parser1.data}, incremental={parser2.data}")
        else:
            print(f"  ✓ '{text}': consistent result {parser1.data}")
    
    # More complex example
    print("\nMore complex example with HTML:")
    html_text = "<div>0123456789</div>"
    
    parser_all = DataCollector()
    parser_all.feed(html_text)
    parser_all.close()
    
    for split_pos in range(1, len(html_text)):
        parser_inc = DataCollector()
        parser_inc.feed(html_text[:split_pos])
        parser_inc.feed(html_text[split_pos:])
        parser_inc.close()
        
        if parser_all.data != parser_inc.data:
            print(f"  Split at {split_pos}: {parser_inc.data} (expected: {parser_all.data})")


if __name__ == "__main__":
    test_control_char_bug()
    test_incremental_feed_bug()