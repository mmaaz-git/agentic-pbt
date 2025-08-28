"""Minimal test case to reproduce the text_compare bug"""

import lxml.doctestcompare as dc

def test_bug():
    checker = dc.LXMLOutputChecker()
    
    # This should match according to the docstring - ... is a wildcard
    # Pattern: literal dot + wildcard + '0'
    # Text: literal dot + 'ABC' + '0'
    pattern = '....0'  
    text = '.ABC0'
    
    result = checker.text_compare(pattern, text, True)
    print(f"Pattern: {pattern!r}")
    print(f"Text: {text!r}")
    print(f"Should match: True")
    print(f"Actually matches: {result}")
    
    assert result, "The pattern '....0' should match '.ABC0' (. followed by wildcard ... followed by 0)"

if __name__ == "__main__":
    test_bug()