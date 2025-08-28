"""Focused test to understand the slash handling bug"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from pyramid.util import text_, bytes_

# Test the exact encoding pattern with a forward slash
def test_slash_encoding():
    """Test how forward slash is handled in the encoding pattern"""
    
    # Original subpath element
    original = '/'
    print(f"Original: {repr(original)}")
    
    # Step 1: UTF-8 encode
    utf8_bytes = original.encode('utf-8')
    print(f"UTF-8 bytes: {utf8_bytes}")
    
    # Step 2: Decode as latin-1 (simulating text_(x.encode('utf-8'), 'latin-1'))
    latin1_str = utf8_bytes.decode('latin-1')
    print(f"As latin-1 string: {repr(latin1_str)}")
    
    # Step 3: Join with '/' separator
    path_info = '/' + '/'.join([latin1_str])
    print(f"PATH_INFO: {repr(path_info)}")
    
    # Step 4: Split and reverse (simulating the workback process)
    parts = path_info.strip('/').split('/') if path_info != '/' else []
    print(f"Split parts: {parts}")
    
    # Step 5: For each part, encode as latin-1 and decode as UTF-8
    reversed_parts = []
    for el in parts:
        latin1_bytes = el.encode('latin-1') 
        utf8_str = latin1_bytes.decode('utf-8')
        reversed_parts.append(utf8_str)
    
    print(f"Reversed parts: {reversed_parts}")
    print(f"Expected: {[original]}")
    
    # The bug: we get [''] instead of ['/']
    assert reversed_parts == [original], f"Got {reversed_parts}, expected {[original]}"

if __name__ == "__main__":
    test_slash_encoding()