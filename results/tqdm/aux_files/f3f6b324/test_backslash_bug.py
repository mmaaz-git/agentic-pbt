"""
Test to demonstrate the backslash handling bug in tqdm.cli.cast
"""
import tqdm.cli
from tqdm.cli import TqdmTypeError


def test_backslash_escape_bug():
    """
    The cast function with 'chr' type fails to handle '\\\\' (escaped backslash).
    
    According to Python escape sequence rules:
    - '\\\\' in a Python string literal represents two backslash characters
    - When this is used as an escape sequence in another string, it represents a single backslash
    - eval('"\\\\\"') produces a string with a single backslash
    
    The bug is in the regex pattern used to detect escape sequences.
    """
    
    # This should work but raises TqdmTypeError
    try:
        result = tqdm.cli.cast('\\\\', 'chr')
        assert result == b'\\', f"Expected single backslash byte, got {result!r}"
        print("PASS: Double backslash handled correctly")
    except TqdmTypeError as e:
        print(f"BUG FOUND: Double backslash raises error: {e}")
        
    # Show that Python's eval would handle this correctly
    expected = eval(r'"\\"').encode()  # Using raw string to be clear
    print(f"Python eval(r'\"\\\\\"').encode() produces: {expected!r}")
    
    # Show the inconsistency
    print("\nInconsistency demonstration:")
    print("  Single backslash (\\\\) -> Passes (incorrectly returns as-is)")
    try:
        result = tqdm.cli.cast('\\', 'chr') 
        print(f"    Result: {result!r}")
    except TqdmTypeError as e:
        print(f"    Error: {e}")
        
    print("  Double backslash (\\\\\\\\) -> Fails (should return single backslash)")
    try:
        result = tqdm.cli.cast('\\\\', 'chr')
        print(f"    Result: {result!r}")
    except TqdmTypeError as e:
        print(f"    Error: {e}")
    
    print("\nOther escape sequences that work:")
    for seq in ['\\n', '\\t', '\\r']:
        result = tqdm.cli.cast(seq, 'chr')
        print(f"  {seq!r} -> {result!r}")


if __name__ == "__main__":
    test_backslash_escape_bug()