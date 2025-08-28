import io
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyatlan_env/lib/python3.13/site-packages')

from pyatlan.multipart_data_generator import MultipartDataGenerator

def analyze_multipart_structure(filename):
    """Analyze the multipart structure for a given filename"""
    gen = MultipartDataGenerator()
    mock_file = io.BytesIO(b"test content")
    gen.add_file(mock_file, filename)
    result = gen.get_post_data()
    
    print(f"\n--- Analyzing filename: {repr(filename)} ---")
    print(f"Raw bytes: {result}")
    print("\nParsing as multipart:")
    
    # Parse according to RFC 2046 / RFC 7578 for multipart/form-data
    boundary = str(gen.boundary).encode()
    parts = result.split(b'--' + boundary)
    
    for i, part in enumerate(parts):
        print(f"\nPart {i}: {repr(part[:200] if len(part) > 200 else part)}")
    
    # Check if this would be correctly parsed by an HTTP server
    # According to RFC 7578, the filename parameter should be escaped
    # Check Content-Disposition header
    if b'Content-Disposition:' in result:
        # Extract the header line
        start = result.find(b'Content-Disposition:')
        end = result.find(b'\r\n', start)
        header = result[start:end]
        print(f"\nContent-Disposition header: {repr(header)}")
        
        # Check if the header is malformed
        if b'\r' in header[20:] or b'\n' in header[20:]:  # Skip the initial "Content-Disposition:"
            print("WARNING: Header contains unescaped CR/LF!")
            return False
        
        if header.count(b'"') % 2 != 0:
            print("WARNING: Unmatched quotes in header!")
            return False
    
    return True

# Test various problematic filenames
test_cases = [
    'normal.txt',
    'test\rfile.txt',  # Carriage return
    'test\nfile.txt',  # Line feed
    'test\r\nfile.txt',  # CRLF
    'test"file.txt',  # Quote
    'test"injected\r\nContent-Type: text/html',  # Header injection attempt
    'test;file.txt',  # Semicolon
    'test\\file.txt',  # Backslash
]

valid_count = 0
for filename in test_cases:
    is_valid = analyze_multipart_structure(filename)
    if is_valid:
        valid_count += 1
    else:
        print(f"INVALID multipart structure for: {repr(filename)}")

print(f"\n\nSummary: {valid_count}/{len(test_cases)} produced valid multipart structures")
print("\nThe issue: Special characters in filenames are not escaped, which can:")
print("1. Break multipart parsing (CR/LF characters)")
print("2. Allow header injection attacks")
print("3. Cause parsing ambiguities (unescaped quotes)")