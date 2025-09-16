#!/usr/bin/env python3
"""Test the impact of the Unicode normalization bug in real Fire usage."""

import fire

def process_text(text):
    """Process some text and return it."""
    return f"Processed: {text}"

def test_micro_sign():
    """Test if the bug affects real Fire CLI usage."""
    # Simulate what happens when a user passes µ as an argument
    import sys
    import fire.core
    
    # Test case 1: User passes µ as argument
    original_argv = sys.argv
    try:
        sys.argv = ['test_impact.py', 'process_text', 'µ']
        result = fire.core.Fire(process_text, command=sys.argv[1:])
        print(f"Fire result for 'µ': {result}")
    finally:
        sys.argv = original_argv
    
    # Direct comparison
    direct_result = process_text('µ')
    print(f"Direct call result: {direct_result}")
    
    # Check what Fire's parser does
    from fire.parser import DefaultParseValue
    parsed = DefaultParseValue('µ')  
    print(f"DefaultParseValue('µ') = '{parsed}' (U+{ord(parsed):04X})")
    
    # This shows the user input gets transformed
    print(f"\nImpact: User inputs 'µ' but function receives 'μ'")
    print(f"This violates the principle that simple strings should pass through unchanged.")

if __name__ == "__main__":
    test_micro_sign()