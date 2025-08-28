"""Demonstrate the text_compare bug with ... wildcard after literal dots"""

import lxml.doctestcompare as dc

def demonstrate_bug():
    checker = dc.LXMLOutputChecker()
    
    print("Testing text_compare with ... wildcard:")
    print("=" * 50)
    
    # Working cases
    print("\nCases that work correctly:")
    
    # Case 1: Simple wildcard
    pattern1 = "hello...world"
    text1 = "hello there world"
    result1 = checker.text_compare(pattern1, text1, True)
    print(f"  Pattern: {pattern1!r} matches {text1!r}: {result1} ✓")
    
    # Case 2: Just wildcard
    pattern2 = "..."
    text2 = "anything"
    result2 = checker.text_compare(pattern2, text2, True)
    print(f"  Pattern: {pattern2!r} matches {text2!r}: {result2} ✓")
    
    print("\nBroken cases (BUG):")
    
    # Bug Case 1: Literal dot followed by wildcard
    pattern3 = "....0"  # One literal dot + ... wildcard + 0
    text3 = ".ABC0"     # One literal dot + ABC + 0
    result3 = checker.text_compare(pattern3, text3, True)
    print(f"  Pattern: {pattern3!r} SHOULD match {text3!r}: {result3} ✗")
    
    # Bug Case 2: Multiple dots followed by wildcard
    pattern4 = "......end"  # Three literal dots + ... wildcard + end
    text4 = "...middleend"  # Three literal dots + middle + end  
    result4 = checker.text_compare(pattern4, text4, True)
    print(f"  Pattern: {pattern4!r} SHOULD match {text4!r}: {result4} ✗")
    
    # Bug Case 3: Pattern ending with dots and wildcard
    pattern5 = "start...."  # start + one literal dot + ... wildcard
    text5 = "start.anything"
    result5 = checker.text_compare(pattern5, text5, True)
    print(f"  Pattern: {pattern5!r} SHOULD match {text5!r}: {result5} ✗")
    
    print("\n" + "=" * 50)
    print("Root cause: When literal dots precede the ... wildcard,")
    print("the regex escaping causes incorrect pattern matching.")
    print("After escaping '....', we get '\\.\\.\\.\\.'")
    print("Then replacing '\\.\\.\\.' with '.*' gives '.*\\.' ")
    print("which requires a literal dot after the wildcard - wrong!")
    
    # Return whether bug was found
    return not (result3 and result4 and result5)

if __name__ == "__main__":
    bug_found = demonstrate_bug()
    if bug_found:
        print("\n✗ BUG CONFIRMED: text_compare fails with dots before wildcard")
    else:
        print("\n✓ No bug found")