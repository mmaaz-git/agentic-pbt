"""
Verify the real-world impact of the chars_to_ranges bug
"""

from Cython.Plex.Regexps import Any
from Cython.Plex import Lexicon, Scanner
from io import StringIO

print("=== Real-world Impact Test ===")
print()
print("The bug causes Any() with duplicate characters to incorrectly")
print("match newlines when it shouldn't.")
print()

# Create a simple lexicon that should only match tab characters
any_tabs = Any('\t\t')
print(f"Created: Any('\\t\\t')")
print(f"  Expected behavior: Match only tab characters")
print(f"  Actual match_nl: {any_tabs.match_nl} (should be 0)")
print()

# Test if this affects actual scanning
print("Testing if this affects actual lexical scanning...")
try:
    # Create a lexicon with our buggy Any() pattern
    from Cython.Plex import TEXT
    lexicon = Lexicon([
        (Any('\t\t'), TEXT),  # Should only match tabs
    ])
    
    # Test strings
    test_inputs = [
        ('\t', "single tab"),
        ('\n', "newline"),
        ('\t\n', "tab then newline"),
    ]
    
    for test_str, description in test_inputs:
        scanner = Scanner(lexicon, StringIO(test_str))
        print(f"Scanning {description} ({repr(test_str)}):")
        try:
            result = scanner.read()
            print(f"  Result: {result}")
            if test_str == '\n' and result != (None, ''):
                print(f"  BUG CONFIRMED: Newline was matched by Any('\\t\\t')!")
        except Exception as e:
            print(f"  Error: {e}")
    print()
    
except Exception as e:
    print(f"Error creating lexicon: {e}")
    print()

print("=== Conclusion ===")
print("The bug in chars_to_ranges causes Any() with duplicate characters")
print("to have incorrect match_nl property. When the duplicate character")
print("has code adjacent to newline (like tab=9, backspace=8, vtab=11),")
print("the resulting range incorrectly includes the newline character.")