"""Demonstrate the whitespace normalization bug in text_compare"""

import lxml.doctestcompare as dc

def demonstrate_bug():
    checker = dc.LXMLOutputChecker()
    
    print('Demonstrating the whitespace normalization bug:')
    print('=' * 60)
    
    # The issue: whitespace normalization is inconsistent
    test_cases = [
        ('a\r...', 'a\r', 'Pattern with \\r at middle + wildcard'),
        ('a\n...', 'a\n', 'Pattern with \\n at middle + wildcard'),
        ('a\t...', 'a\t', 'Pattern with \\t at middle + wildcard'),
        ('a  ...', 'a  ', 'Pattern with double space + wildcard'),
        ('0\r...', '0\r', 'Original failing case'),
    ]
    
    print("\nThese patterns should match (... can match empty string):")
    print("-" * 60)
    
    failures = []
    for pattern, text, description in test_cases:
        result = checker.text_compare(pattern, text, strip=True)
        status = '✓' if result else '✗ FAIL'
        print(f'{description:40} | {status}')
        if not result:
            failures.append((pattern, text, description))
    
    if failures:
        print("\n" + "=" * 60)
        print("BUG FOUND: Whitespace normalization inconsistency")
        print("=" * 60)
        print("\nRoot cause analysis:")
        print("-" * 60)
        
        # Show what happens with one failing case
        pattern, text, _ = failures[0]
        print(f"\nExample: pattern={pattern!r}, text={text!r}")
        
        # Simulate what text_compare does
        want = pattern
        got = text
        
        # With strip=True, normalization happens
        want_norm = dc.norm_whitespace(want).strip()
        got_norm = dc.norm_whitespace(got).strip()
        
        print(f"After norm_whitespace + strip:")
        print(f"  Pattern becomes: {want_norm!r}")
        print(f"  Text becomes: {got_norm!r}")
        print(f"\nThe problem: The pattern keeps internal whitespace while")
        print(f"the text has it normalized, leading to a mismatch.")
        
        return True
    
    return False

if __name__ == "__main__":
    bug_found = demonstrate_bug()
    if bug_found:
        print("\n✗ BUG CONFIRMED")
    else:
        print("\n✓ No bug found")