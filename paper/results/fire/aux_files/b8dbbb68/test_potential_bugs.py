"""Tests specifically designed to find potential bugs."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, example
from fire import custom_descriptions, formatting


@settings(max_examples=5000)
@given(st.text(min_size=0, max_size=1000), 
       st.integers(min_value=-100, max_value=1000),
       st.integers(min_value=-100, max_value=1000))
def test_get_summary_comprehensive(text, available_space, line_length):
    """Comprehensive test for GetSummary to find any bugs."""
    try:
        result = custom_descriptions.GetSummary(text, available_space, line_length)
        
        # Basic format check
        assert result.startswith('"'), f"Should start with quote: {result}"
        assert result.endswith('"'), f"Should end with quote: {result}"
        
        # Extract content
        content = result[1:-1]
        
        # Length checks
        if available_space >= 5 and line_length >= 5:
            # Should respect limits
            if available_space >= len(text) + 2:
                # Should show full text
                assert content == text, f"Should show full text when space available"
            elif available_space >= 5:
                # Should be truncated to fit
                assert len(result) <= max(available_space, 5), \
                    f"Length {len(result)} exceeds limit {available_space}"
        
        # Ellipsis check
        if content.endswith('...') and len(content) > 3:
            # The non-ellipsis part should be from the original text
            non_ellipsis = content[:-3]
            assert text.startswith(non_ellipsis), \
                f"Truncated part '{non_ellipsis}' should be start of '{text}'"
                
    except Exception as e:
        print(f"Error with text='{text}', available_space={available_space}, line_length={line_length}")
        print(f"Error: {e}")
        raise


@settings(max_examples=5000)
@given(st.text(min_size=0, max_size=1000), 
       st.integers(min_value=-100, max_value=1000),
       st.integers(min_value=-100, max_value=1000))
def test_ellipsis_truncate_comprehensive(text, available_space, line_length):
    """Comprehensive test for EllipsisTruncate to find bugs."""
    try:
        result = formatting.EllipsisTruncate(text, available_space, line_length)
        
        # Should never exceed the limit when space >= 3
        if available_space >= 3:
            if len(text) <= available_space:
                assert result == text, "Should not truncate when text fits"
            else:
                assert len(result) == available_space, \
                    f"Result length {len(result)} should equal available_space {available_space}"
                assert result.endswith('...'), "Should end with ellipsis when truncated"
                # Check the truncated part matches original
                assert result[:-3] == text[:available_space-3], \
                    "Truncated part should match original text"
        else:
            # When available_space < 3, should use line_length
            if available_space < 3 and line_length >= 3:
                if len(text) <= line_length:
                    assert result == text
                else:
                    assert len(result) == line_length
                    assert result.endswith('...')
                    
    except Exception as e:
        print(f"Error with text='{text[:50]}...', available_space={available_space}, line_length={line_length}")
        print(f"Error: {e}")
        raise


@settings(max_examples=2000)
@given(st.text(alphabet=st.characters(min_codepoint=0x0, max_codepoint=0x10FFFF), 
               min_size=0, max_size=100),
       st.integers(min_value=0, max_value=100))
def test_unicode_handling(text, available_space):
    """Test handling of various Unicode characters including emojis and special chars."""
    line_length = 100
    
    try:
        # Test GetSummary
        summary = custom_descriptions.GetSummary(text, available_space, line_length)
        assert summary.startswith('"') and summary.endswith('"')
        
        # Test GetDescription  
        description = custom_descriptions.GetDescription(text, available_space, line_length)
        assert description.startswith('The string "')
        
        # Test EllipsisTruncate
        truncated = formatting.EllipsisTruncate(text, available_space, line_length)
        
        # Basic sanity checks
        if available_space >= 3 and len(text) > available_space:
            assert truncated.endswith('...')
            
    except Exception as e:
        print(f"Unicode handling error with text containing codepoints")
        print(f"Error: {e}")
        raise


@settings(max_examples=1000)
@given(st.text(min_size=1, max_size=50))
def test_get_string_type_summary_directly(text):
    """Test GetStringTypeSummary function directly."""
    for available_space in [0, 1, 2, 3, 4, 5, 10, 20, 50, 100]:
        line_length = 80
        result = custom_descriptions.GetStringTypeSummary(text, available_space, line_length)
        
        # Should always be quoted
        assert result.startswith('"') and result.endswith('"')
        
        # Content check
        content = result[1:-1]
        if len(text) + 2 <= available_space:
            assert content == text
        else:
            if available_space >= 5:
                assert content.endswith('...')


@settings(max_examples=1000)
@given(st.text(min_size=0, max_size=50), 
       st.integers(min_value=0, max_value=100))
def test_get_string_type_description_directly(text, available_space):
    """Test GetStringTypeDescription function directly."""
    line_length = 80
    result = custom_descriptions.GetStringTypeDescription(text, available_space, line_length)
    
    # Should always have the right format
    assert result.startswith('The string "')
    assert result.endswith('"')
    
    # Extract the string part
    content = result[len('The string "'):-1]
    
    # Check truncation
    full_length = len('The string "') + len(text) + 1
    if full_length <= available_space:
        assert content == text
    elif available_space >= len('The string "..."'):
        assert content.endswith('...')


@settings(max_examples=2000)
@given(st.integers(min_value=0, max_value=200), 
       st.integers(min_value=0, max_value=200))
def test_consistency_between_functions(available_space, line_length):
    """Test consistency between GetSummary and GetStringTypeSummary."""
    test_string = "Test String For Consistency"
    
    # These should produce the same result for strings
    summary1 = custom_descriptions.GetSummary(test_string, available_space, line_length)
    summary2 = custom_descriptions.GetStringTypeSummary(test_string, available_space, line_length)
    
    assert summary1 == summary2, f"GetSummary and GetStringTypeSummary should match: '{summary1}' != '{summary2}'"
    
    # Same for GetDescription
    desc1 = custom_descriptions.GetDescription(test_string, available_space, line_length)
    desc2 = custom_descriptions.GetStringTypeDescription(test_string, available_space, line_length)
    
    assert desc1 == desc2, f"GetDescription and GetStringTypeDescription should match: '{desc1}' != '{desc2}'"


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v', '--tb=short'])