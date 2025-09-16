"""Test version specifier edge cases"""

from packaging.requirements import Requirement, InvalidRequirement
from packaging.specifiers import InvalidSpecifier

print("Testing version specifier edge cases:")

test_cases = [
    # Edge cases with dots
    ("package>=1.", "Version ending with dot"),
    ("package>=.1", "Version starting with dot"),
    ("package>=1..0", "Double dot"),
    ("package>=.", "Just dot"),
    
    # Empty versions
    ("package>=", "Empty version after operator"),
    ("package==", "Empty version with =="),
    
    # Multiple operators
    ("package>=>1.0", "Double operator >=>"),
    ("package=>=1.0", "Wrong order =>="),
    
    # Spaces in versions
    ("package>=1. 0", "Space in version"),
    ("package>= 1.0", "Space after operator"),
    
    # Special version strings
    ("package>=*", "Wildcard version"),
    ("package>=1.*", "Partial wildcard"),
    ("package>=1.0.0.0.0", "Many parts"),
    
    # Case sensitivity
    ("package>=1.0A", "Letter in version"),
    ("package>=1.0rc1", "Release candidate"),
]

for req_str, description in test_cases:
    print(f"\n{description}: '{req_str}'")
    try:
        req = Requirement(req_str)
        print(f"  ✓ Parsed successfully")
        print(f"    Name: {req.name}")
        print(f"    Specifier: {req.specifier}")
        print(f"    String repr: {str(req)}")
        
        # Test round-trip
        try:
            req2 = Requirement(str(req))
            if str(req) == str(req2):
                print(f"    Round-trip: OK")
            else:
                print(f"    Round-trip: MISMATCH - '{str(req)}' != '{str(req2)}'")
        except Exception as e:
            print(f"    Round-trip: FAILED - {e}")
            
    except InvalidRequirement as e:
        print(f"  ✗ InvalidRequirement: {e}")
    except Exception as e:
        print(f"  ✗ Unexpected error: {type(e).__name__}: {e}")

print("\n" + "="*60)
print("Testing whitespace in version specifiers:")

# More whitespace tests
whitespace_tests = [
    "package >= 1.0",
    "package >=1.0",
    "package>= 1.0",
    "package\t>=\t1.0",
    "package\n>=\n1.0",
]

for req_str in whitespace_tests:
    print(f"\n'{repr(req_str)}'")
    try:
        req = Requirement(req_str)
        print(f"  Parsed: {str(req)}")
    except Exception as e:
        print(f"  Error: {e}")