"""Test for actual encoding bugs in call_app_with_subpath_as_path_info"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from unittest.mock import Mock
from pyramid.request import call_app_with_subpath_as_path_info

def test_unicode_subpath():
    """Test subpath with Unicode characters that break the encoding pattern"""
    
    test_cases = [
        # (subpath_element, description)
        ("Ā", "Latin Extended-A character (U+0100)"),
        ("€", "Euro sign (U+20AC)"),
        ("🦄", "Emoji (U+1F984)"),
        ("测试", "Chinese characters"),
        ("\x80", "High ASCII character"),
    ]
    
    for test_char, description in test_cases:
        print(f"\nTesting: {description}")
        print(f"Character: {repr(test_char)}")
        
        request = Mock()
        request.subpath = [test_char]
        request.environ = {
            'SCRIPT_NAME': '',
            'PATH_INFO': '/test'
        }
        
        new_request = Mock()
        new_request.environ = {}
        new_request.get_response = Mock(return_value="response")
        request.copy = Mock(return_value=new_request)
        
        app = Mock()
        
        try:
            # Call the function
            result = call_app_with_subpath_as_path_info(request, app)
            
            # Get the resulting PATH_INFO
            path_info = new_request.environ.get('PATH_INFO', '')
            print(f"Resulting PATH_INFO: {repr(path_info)}")
            
            # Try to extract the character back
            if path_info and path_info != '/':
                # Remove leading slash and decode
                extracted = path_info[1:]  # Remove leading /
                
                # The function uses text_(x.encode('utf-8'), 'latin-1')
                # So path_info contains UTF-8 bytes interpreted as latin-1
                # To reverse: encode as latin-1, decode as UTF-8
                try:
                    recovered_bytes = extracted.encode('latin-1')
                    recovered_char = recovered_bytes.decode('utf-8')
                    print(f"Recovered character: {repr(recovered_char)}")
                    
                    if recovered_char == test_char:
                        print("✓ Round-trip successful")
                    else:
                        print(f"✗ Round-trip failed: {repr(test_char)} -> {repr(recovered_char)}")
                except Exception as e:
                    print(f"✗ Recovery failed: {e}")
                    
        except Exception as e:
            print(f"✗ Function call failed: {e}")

def test_problematic_encoding_pattern():
    """Direct test of the problematic encoding pattern"""
    
    # Character that takes 2 bytes in UTF-8
    char = "Ā"  # U+0100
    print(f"\nDirect encoding test for: {repr(char)}")
    
    # Step 1: Encode to UTF-8
    utf8_bytes = char.encode('utf-8')
    print(f"UTF-8 bytes: {utf8_bytes.hex()} ({utf8_bytes})")
    
    # Step 2: Interpret these bytes as latin-1
    # This is what text_(x.encode('utf-8'), 'latin-1') does
    latin1_interpretation = utf8_bytes.decode('latin-1') 
    print(f"Interpreted as latin-1: {repr(latin1_interpretation)}")
    
    # Step 3: Try to reverse - encode as latin-1
    try:
        latin1_bytes = latin1_interpretation.encode('latin-1')
        print(f"Re-encoded to latin-1: {latin1_bytes.hex()} ({latin1_bytes})")
        
        # Step 4: Decode as UTF-8
        utf8_result = latin1_bytes.decode('utf-8')
        print(f"Decoded as UTF-8: {repr(utf8_result)}")
        
        if utf8_result == char:
            print("✓ Encoding round-trip successful")
        else:
            print(f"✗ Encoding round-trip failed")
            
    except Exception as e:
        print(f"✗ Encoding failed: {e}")

if __name__ == "__main__":
    test_problematic_encoding_pattern()
    test_unicode_subpath()