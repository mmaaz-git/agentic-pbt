"""
Minimal reproduction of the overflow bug in dateutil.parser.
"""
import dateutil.parser

# This causes an OverflowError
print("Testing: '000010000000000'")
try:
    result = dateutil.parser.parse('000010000000000')
    print(f"Result: {result}")
except OverflowError as e:
    print(f"OverflowError: {e}")
    print("\nThis is a bug - the parser should either:")
    print("1. Reject the input with a ParserError, or")
    print("2. Handle the large number gracefully")
    print("But it should NOT crash with an unhandled OverflowError")