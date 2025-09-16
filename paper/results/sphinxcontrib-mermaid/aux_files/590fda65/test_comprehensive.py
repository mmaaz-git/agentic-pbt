#!/usr/bin/env python3
"""Comprehensive property-based tests with more examples."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sphinxcontrib-mermaid_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings

# Test with many examples
@settings(max_examples=5000)
@given(st.text())
def test_math_splitting_comprehensive(text):
    """Comprehensive test of math block splitting."""
    parts = text.split('\n\n')
    
    # The split should be reversible
    rejoined = '\n\n'.join(parts)
    assert rejoined == text
    
    # Count consistency
    delimiter_count = text.count('\n\n')
    if delimiter_count == 0:
        assert len(parts) == 1
    else:
        assert len(parts) == delimiter_count + 1


@settings(max_examples=5000)
@given(st.text(alphabet='0123456789.', min_size=1, max_size=20))
def test_version_parsing_comprehensive(version_str):
    """Comprehensive version parsing test."""
    # Skip invalid versions
    if version_str.startswith('.') or version_str.endswith('.') or '..' in version_str or version_str == '.':
        return
    
    parts = version_str.split('.')
    if not all(part.isdigit() and part != '' for part in parts):
        return
    
    try:
        version_info = tuple(map(int, version_str.split('.')))
        
        # Should successfully parse
        assert isinstance(version_info, tuple)
        assert len(version_info) == len(parts)
        
        # Values should match
        for i, part in enumerate(parts):
            assert version_info[i] == int(part)
            
    except ValueError:
        # Should only fail for non-numeric parts
        assert not all(part.isdigit() for part in parts)


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])