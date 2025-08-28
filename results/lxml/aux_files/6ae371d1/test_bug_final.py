"""Final bug reproduction for lxml.doctestcompare text_compare"""

import lxml.doctestcompare as dc

def reproduce_bug():
    """Reproduce the text_compare whitespace normalization bug"""
    
    checker = dc.LXMLOutputChecker()
    
    # Bug: When a pattern ends with whitespace followed by ..., 
    # and the text ends with the same whitespace, the comparison fails
    # because strip=True removes trailing whitespace inconsistently
    
    # Minimal failing case from property test
    pattern = '0\r...'
    text = '0\r'
    
    print("BUG: text_compare with whitespace normalization")
    print("=" * 50)
    print(f"Pattern: {pattern!r}")
    print(f"Text: {text!r}")
    print(f"Expected: True (... should match empty string)")
    
    result = checker.text_compare(pattern, text, strip=True)
    print(f"Actual: {result}")
    
    if not result:
        print("\n✗ BUG CONFIRMED!")
        print("\nRoot cause:")
        print("- norm_whitespace regex is [ \\t\\n][ \\t\\n]+ which doesn't include \\r")
        print("- So '0\\r' becomes '0\\r' after norm_whitespace")
        print("- Then strip() removes the trailing \\r from text, giving '0'")
        print("- But pattern '0\\r...' stays as '0\\r...' after normalization")
        print("- The final regex '^0\\r.*$' doesn't match '0'")
        
        # Additional test cases showing the issue
        print("\nOther affected cases:")
        test_cases = [
            ('a\r...', 'a\r', 'Carriage return'),
            ('x\r\n...', 'x\r\n', 'CRLF line ending'),
            ('y\v...', 'y\v', 'Vertical tab'),
            ('z\f...', 'z\f', 'Form feed'),
        ]
        
        for pat, txt, desc in test_cases:
            res = checker.text_compare(pat, txt, strip=True)
            print(f"  {desc:20}: pattern={pat!r:12} text={txt!r:8} -> {res}")
        
        return True
    
    return False

if __name__ == "__main__":
    reproduce_bug()