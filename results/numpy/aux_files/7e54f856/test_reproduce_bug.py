"""Reproduce the markoutercomma bug with minimal example."""

import numpy.f2py.crackfortran as cf

# Test cases that should be handled gracefully
test_cases = [
    ')',        # Unmatched closing paren
    '))',       # Multiple unmatched closing
    '(',        # Unmatched opening paren  
    '((', 
    '())',      # Extra closing
    '(()',      # Missing closing
    ',)',       # Comma with unmatched paren
    '(,',       # 
    'a,b)',     # Realistic: unmatched in function arg
    'func(a,b))', # Extra paren in function call
]

print("Testing markoutercomma with potentially malformed inputs:")
print("=" * 60)

for test_input in test_cases:
    try:
        result = cf.markoutercomma(test_input)
        print(f"✓ markoutercomma({test_input!r}) = {result!r}")
    except AssertionError as e:
        print(f"✗ markoutercomma({test_input!r}) raises AssertionError: {e}")
    except Exception as e:
        print(f"✗ markoutercomma({test_input!r}) raises {type(e).__name__}: {e}")

print("\n" + "=" * 60)
print("Summary: markoutercomma fails on unbalanced parentheses with AssertionError")
print("This could cause crashes when parsing malformed Fortran code.")