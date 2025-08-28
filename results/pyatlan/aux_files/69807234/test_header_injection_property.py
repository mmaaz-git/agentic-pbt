import io
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyatlan_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, example
from pyatlan.multipart_data_generator import MultipartDataGenerator

# Property-based test that found the security vulnerability
@given(st.text(min_size=1, max_size=100))
@example('test.txt\r\nX-Injected: value')  # Header injection
@example('test"breakout')  # Quote breakout
def test_no_header_injection(filename):
    """Filenames should not allow header injection attacks"""
    gen = MultipartDataGenerator()
    mock_file = io.BytesIO(b"content")
    gen.add_file(mock_file, filename)
    result = gen.get_post_data()
    
    # Count occurrences of headers that should only appear once per part
    content_type_count = result.count(b'Content-Type:')
    content_disposition_count = result.count(b'Content-Disposition:')
    
    # In a properly formed multipart with one file:
    # - Content-Disposition should appear exactly twice (once for "name", once for "file")
    # - Content-Type should appear exactly once (for the file)
    
    # This assertion fails when header injection is possible
    assert content_type_count == 1, f"Found {content_type_count} Content-Type headers, expected 1"
    assert content_disposition_count == 2, f"Found {content_disposition_count} Content-Disposition headers, expected 2"
    
    # Also check that filename parameter is properly quoted/escaped
    # The filename should not be able to break out of its quotes
    if b'filename="' in result:
        # Extract the filename parameter
        start = result.find(b'filename="')
        # Find the end quote - should be before any CRLF
        end_section = result[start:start+1000]
        # The closing quote should come before any CRLF (except the one at end of header)
        quote_end = end_section.find(b'"', 10)  # Skip the opening quote
        crlf_pos = end_section.find(b'\r\n')
        
        # The quote should close before the CRLF
        assert quote_end < crlf_pos, "Filename contains unescaped characters that break out of quotes"

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, '-v', '--tb=short'])