"""
Test revealing Unicode alphanumeric validation inconsistency
"""
from hypothesis import given, strategies as st
import troposphere.synthetics as synthetics
import re


# Generate Unicode alphanumeric characters that are not ASCII
@given(st.characters().filter(lambda c: c.isalnum() and not c.isascii()))
def test_unicode_alphanumeric_validation_inconsistency(char):
    """
    Python's isalnum() accepts Unicode alphanumeric characters,
    but troposphere's validation regex only accepts ASCII [a-zA-Z0-9].
    
    This creates a validation bypass when using Python's isalnum() to
    pre-filter inputs, as these characters will pass isalnum() but
    fail the actual validation.
    """
    # Character passes Python's isalnum() check
    assert char.isalnum()
    
    # But fails troposphere's validation
    valid_names = re.compile(r'^[a-zA-Z0-9]+$')
    assert not valid_names.match(char)
    
    # This will raise ValueError even though isalnum() returns True
    try:
        group = synthetics.Group(char, Name="TestGroup")
        assert False, f"Should have raised ValueError for {char!r}"
    except ValueError as e:
        assert 'not alphanumeric' in str(e)


if __name__ == "__main__":
    # Demonstrate the inconsistency
    print("Unicode characters that are 'alphanumeric' but fail validation:")
    
    examples = ['¹', '²', '³', 'α', 'β', 'ñ', 'é', '中']
    
    for char in examples:
        print(f"\nCharacter: {char!r}")
        print(f"  Python isalnum(): {char.isalnum()}")
        print(f"  ASCII only: {char.isascii()}")
        
        try:
            group = synthetics.Group(char, Name="TestGroup")
            print(f"  Validation: ✓ Accepted")
        except ValueError as e:
            print(f"  Validation: ✗ Rejected - {e}")
    
    print("\nThe inconsistency: Python's isalnum() accepts Unicode alphanumeric")
    print("characters, but AWS CloudFormation requires ASCII-only [a-zA-Z0-9].")