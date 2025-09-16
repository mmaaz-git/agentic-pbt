#!/usr/bin/env python3
"""Minimal test demonstrating control character bug in stylesheet_params."""

import lxml.isoschematron as iso
from hypothesis import given, strategies as st, settings

@given(st.text(min_size=1))
@settings(max_examples=1000)
def test_stylesheet_params_control_character_crash(text):
    """Test that stylesheet_params handles all valid Python strings."""
    # This function is documented to wrap strings with XSLT.strparam()
    # but doesn't document that control characters will cause crashes
    try:
        result = iso.stylesheet_params(param=text)
        # Should succeed for all valid Python strings
        assert 'param' in result
    except ValueError as e:
        # Check if it's the control character error
        if "All strings must be XML compatible" in str(e):
            # This is the bug - the function crashes on valid Python strings
            # containing control characters without documenting this limitation
            assert any(ord(c) < 32 and c not in '\t\n\r' for c in text), \
                f"ValueError raised for text without control chars: {repr(text)}"
            # Found the bug - report it
            print(f"BUG FOUND: stylesheet_params crashes on control character {repr(text[0])}")
            raise
        else:
            # Some other ValueError - re-raise
            raise

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])