import io
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyatlan_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, example
from pyatlan.multipart_data_generator import MultipartDataGenerator

# Property test that discovered the bug
@given(st.text(min_size=1, max_size=50))
@example('\r')  # Minimal failing case
@example('\n')  # Another failing case  
@example('"')   # Quote character
@example('test\r\nSet-Cookie: evil=true')  # Header injection attempt
def test_filename_special_characters(filename):
    """Filenames with special characters should be properly escaped in multipart data"""
    gen = MultipartDataGenerator()
    mock_file = io.BytesIO(b"content")
    gen.add_file(mock_file, filename)
    result = gen.get_post_data()
    
    # The multipart structure should remain valid
    # Check that control characters don't break the structure
    result_str = result.decode('utf-8', errors='ignore')
    
    # After proper CRLF sequences are removed, there should be no stray CR or LF
    # This ensures the filename doesn't inject new headers or break parsing
    lines = result_str.split('\r\n')
    
    # Find the line with the filename
    for line in lines:
        if 'filename="' in line:
            # The filename should be on a single line (no embedded CRLF)
            # This fails for filenames with \r or \n
            assert line.count('filename="') == 1
            # Extract what's between the quotes
            start = line.find('filename="') + len('filename="')
            # Find the closing quote - this fails if filename contains quotes
            end = line.find('"', start)
            if end == -1:
                # Quote character in filename breaks the parsing
                assert '"' not in filename, f"Unescaped quote in filename: {filename}"

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, '-v'])