import pytest
from hypothesis import given, strategies as st, settings, example
from bs4.dammit import EntitySubstitution
import html

# Focus on the quoted_attribute_value function with tricky inputs
@given(text=st.text())
@example(text='"')  # Just a double quote
@example(text="'")  # Just a single quote
@example(text='"\'')  # Both quotes
@example(text='\'"\'"\'')  # Complex mix
@example(text='<>&"\'')  # Special HTML chars with quotes
def test_quoted_attribute_value_comprehensive(text):
    """Comprehensive test of quoted_attribute_value function."""
    result = EntitySubstitution.quoted_attribute_value(text)
    
    # Basic properties that should always hold
    assert len(result) >= 2, f"Result too short for input '{text}': {result}"
    quote_char = result[0]
    assert quote_char in ['"', "'"], f"Invalid quote char: {quote_char}"
    assert result[-1] == quote_char, f"Mismatched quotes: {result}"
    
    # Extract the content between quotes
    content = result[1:-1]
    
    # Now let's check if the quoting strategy makes sense
    has_single = "'" in text
    has_double = '"' in text
    
    # According to the implementation:
    # 1. If text has & < or >, it's escaped with html.escape(quote=False)
    # 2. If escaped text has double quote but no single quote, use single quotes
    # 3. If escaped text has single quote but no double quote, use double quotes
    # 4. Otherwise (both or neither), use double quotes
    
    escaped_text = text
    if ("&" in text or "<" in text or ">" in text):
        escaped_text = html.escape(text, quote=False)
    
    # Check the quote choice logic
    escaped_has_double = '"' in escaped_text
    escaped_has_single = "'" in escaped_text
    
    if escaped_has_double and not escaped_has_single:
        # Should use single quotes
        assert quote_char == "'", f"Should use single quotes for text with only double quotes: {text}"
        # Content should match escaped text
        assert content == escaped_text, f"Content mismatch: {content} != {escaped_text}"
    elif escaped_has_single and not escaped_has_double:
        # Should use double quotes
        assert quote_char == '"', f"Should use double quotes for text with only single quotes: {text}"
        # Content should match escaped text  
        assert content == escaped_text, f"Content mismatch: {content} != {escaped_text}"
    else:
        # Both or neither - should use double quotes
        assert quote_char == '"', f"Should use double quotes when both types present: {text}"
        # Content should match escaped text
        assert content == escaped_text, f"Content mismatch: {content} != {escaped_text}"


# Test potential bug when text has both quotes
def test_quoted_attribute_value_with_both_quotes_bug():
    """Test specific case where both quote types are present."""
    # This value has both types of quotes
    value = 'Hello "world" and \'universe\''
    
    result = EntitySubstitution.quoted_attribute_value(value)
    print(f"Input: {value}")
    print(f"Result: {result}")
    
    # According to the code, when both quotes are present, it uses double quotes
    # But the content inside isn't escaped! This could be a bug.
    assert result[0] == '"', "Should use double quotes when both present"
    
    # Extract content
    content = result[1:-1]
    
    # The content should be the same as the input since no HTML escaping needed
    # But having unescaped double quotes inside double-quoted string is problematic!
    assert content == value
    
    # This means the result is: "Hello "world" and 'universe'"
    # Which is INVALID as an HTML attribute! The inner quotes break the attribute.
    
    # Let's verify this is indeed problematic
    # An HTML parser would see this as: attribute="Hello " with extra junk after
    
    # Check if the result is valid by counting quotes
    if result[0] == '"':
        # Count unescaped double quotes in content (excluding the outer quotes)
        unescaped_doubles = content.count('"')
        if unescaped_doubles > 0:
            print(f"WARNING: Potential bug found! Unescaped double quotes ({unescaped_doubles}) inside double-quoted attribute value")
            print(f"This would create invalid HTML: {result}")
            # This is likely a BUG!
            return False
    
    return True


# More systematic test for the both-quotes bug
@given(
    prefix=st.text(alphabet="abcdefghijklmnopqrstuvwxyz ", min_size=0, max_size=5),
    middle=st.text(alphabet="abcdefghijklmnopqrstuvwxyz ", min_size=0, max_size=5),
    suffix=st.text(alphabet="abcdefghijklmnopqrstuvwxyz ", min_size=0, max_size=5)
)
def test_both_quotes_systematic(prefix, middle, suffix):
    """Systematically test values with both quote types."""
    # Create a value with both quotes
    value = f'{prefix}"{middle}\'{suffix}'
    
    result = EntitySubstitution.quoted_attribute_value(value)
    
    # If using double quotes as outer quotes
    if result[0] == '"':
        content = result[1:-1]
        # Check for unescaped double quotes in content
        if '"' in content:
            # This is a bug - we have unescaped double quotes inside a double-quoted string
            print(f"\nBUG FOUND!")
            print(f"Input: {value}")
            print(f"Result: {result}")
            print(f"Unescaped double quotes inside double-quoted attribute!")
            
            # Create a minimal reproducer
            minimal = '"test\'test'  # Minimal case with both quotes
            minimal_result = EntitySubstitution.quoted_attribute_value(minimal)
            print(f"Minimal reproducer: EntitySubstitution.quoted_attribute_value('{minimal}')")
            print(f"Minimal result: {minimal_result}")
            
            assert False, f"Bug: Unescaped quotes in attribute value. Input: {value}, Result: {result}"


# Test to verify the bug
def test_verify_quoted_attribute_bug():
    """Verify the quoted_attribute_value bug with a simple example."""
    # Simple test case with both quote types
    value = 'foo"bar\'baz'
    result = EntitySubstitution.quoted_attribute_value(value)
    
    print(f"\n=== INVESTIGATING POTENTIAL BUG ===")
    print(f"Input value: {value}")
    print(f"Result: {result}")
    
    # Parse the result
    quote_char = result[0]
    content = result[1:-1]
    
    print(f"Quote character used: {quote_char}")
    print(f"Content between quotes: {content}")
    
    # Check if this creates invalid HTML
    if quote_char == '"' and '"' in content:
        print("ERROR: Unescaped double quotes found inside double-quoted string!")
        print("This creates INVALID HTML attribute syntax.")
        print(f"The HTML would be: <tag attr={result}>")
        print("An HTML parser would incorrectly parse this.")
        
        # Demonstrate the issue
        print("\nExample of the problem:")
        print(f'  Input: {value}')
        print(f'  Output: {result}')
        print(f'  HTML: <div attr={result}>')
        print(f'  Parser sees: <div attr="foo" bar\'baz>')  # Broken!')
        
        return False  # Bug found
    elif quote_char == "'" and "'" in content:
        print("ERROR: Unescaped single quotes found inside single-quoted string!")
        return False
    
    print("No issue found with this value")
    return True


if __name__ == "__main__":
    print("Testing quoted_attribute_value for bugs...")
    
    # First run the verification test
    print("\n1. Running verification test...")
    has_bug = not test_verify_quoted_attribute_bug()
    
    if has_bug:
        print("\n!!! BUG DETECTED IN quoted_attribute_value !!!")
    
    # Run all tests
    print("\n2. Running comprehensive tests...")
    pytest.main([__file__, "-v", "--tb=short", "-x"])  # -x stops on first failure