import io
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyatlan_env/lib/python3.13/site-packages')

from pyatlan.multipart_data_generator import MultipartDataGenerator

# Minimal reproduction of the bug
def reproduce_bug():
    # Test with filename containing carriage return
    gen = MultipartDataGenerator()
    mock_file = io.BytesIO(b"test content")
    
    # Use a filename with carriage return character
    filename_with_cr = "test\rfile.txt"
    gen.add_file(mock_file, filename_with_cr)
    
    result = gen.get_post_data()
    
    # Show the generated data
    print("Generated multipart data:")
    print(repr(result))
    print("\n")
    
    # Check if the structure is broken
    result_str = result.decode('utf-8', errors='ignore')
    
    # The issue: carriage return in filename breaks the multipart structure
    # because it's not escaped, causing malformed HTTP headers
    print("Issue: Carriage return in filename breaks multipart structure")
    print(f"Filename used: {repr(filename_with_cr)}")
    print("\nExtracted filename from output:")
    if b'filename="' in result:
        start = result.find(b'filename="') + len(b'filename="')
        end = result.find(b'"', start)
        extracted = result[start:end]
        print(f"Extracted: {repr(extracted)}")
    
    # Additional test with newline character
    print("\n--- Testing with newline character ---")
    gen2 = MultipartDataGenerator()
    mock_file2 = io.BytesIO(b"test content")
    filename_with_lf = "test\nfile.txt"
    gen2.add_file(mock_file2, filename_with_lf)
    result2 = gen2.get_post_data()
    print(f"Filename with LF: {repr(filename_with_lf)}")
    print(f"Result snippet: {repr(result2[100:200])}")
    
    # Test with quotes in filename
    print("\n--- Testing with quotes in filename ---")
    gen3 = MultipartDataGenerator()
    mock_file3 = io.BytesIO(b"test content")
    filename_with_quote = 'test"file.txt'
    gen3.add_file(mock_file3, filename_with_quote)
    result3 = gen3.get_post_data()
    print(f"Filename with quote: {repr(filename_with_quote)}")
    print(f"Result snippet: {repr(result3[100:200])}")

if __name__ == "__main__":
    reproduce_bug()