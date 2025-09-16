#!/usr/bin/env python3
"""
Focused test for split_string_literal edge cases.
"""

import Cython.Compiler.StringEncoding as SE
from hypothesis import given, strategies as st, settings, example

# Test split_string_literal with specific edge cases
@given(st.text(min_size=0, max_size=100), 
       st.integers(min_value=-10, max_value=10000))
@settings(max_examples=100)
@example("test", 0)
@example("test", -1)
@example("a" * 100, 1)
def test_split_string_literal_limits(s, limit):
    """Test split_string_literal with various limit values."""
    print(f"Testing with string length {len(s)}, limit {limit}")
    
    if limit <= 0:
        # What happens with non-positive limits?
        try:
            result = SE.split_string_literal(s, limit)
            print(f"  Result with limit {limit}: {result[:50]}...")
            
            # With limit <= 0, the function might behave unexpectedly
            if limit == 0:
                # This could cause infinite loop or error
                pass
        except Exception as e:
            print(f"  Exception with limit {limit}: {e}")
    else:
        result = SE.split_string_literal(s, limit)
        
        if len(s) < limit:
            assert result == s, f"Expected unchanged string for len={len(s)}, limit={limit}"
        else:
            # Check the structure of the result
            chunks = result.split('""')
            print(f"  Split into {len(chunks)} chunks")
            
            # Verify we can reconstruct the original
            rejoined = ''.join(chunks)
            assert rejoined == s, f"Failed to reconstruct: {rejoined[:50]} != {s[:50]}"


if __name__ == "__main__":
    test_split_string_literal_limits()