"""Test for bug in the workback logic of call_app_with_subpath_as_path_info"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from unittest.mock import Mock
from pyramid.request import call_app_with_subpath_as_path_info
from pyramid.util import text_, bytes_

def test_workback_with_unicode():
    """Test the workback logic with Unicode in original PATH_INFO"""
    
    # Set up a request where the original PATH_INFO contains Unicode
    request = Mock()
    request.subpath = ['test']  # Simple ASCII subpath
    
    # PATH_INFO with Unicode character that can't be encoded to latin-1
    request.environ = {
        'SCRIPT_NAME': '',
        'PATH_INFO': '/Ā/test'  # Ā is U+0100, not in latin-1
    }
    
    new_request = Mock()
    new_request.environ = {}
    new_request.get_response = Mock(return_value="response")
    request.copy = Mock(return_value=new_request)
    
    app = Mock()
    
    print(f"Original PATH_INFO: {repr(request.environ['PATH_INFO'])}")
    print(f"Subpath: {request.subpath}")
    
    try:
        # This should fail in the workback logic
        result = call_app_with_subpath_as_path_info(request, app)
        
        print(f"New SCRIPT_NAME: {repr(new_request.environ.get('SCRIPT_NAME', ''))}")
        print(f"New PATH_INFO: {repr(new_request.environ.get('PATH_INFO', ''))}")
        
    except UnicodeEncodeError as e:
        print(f"\n✗ UnicodeEncodeError in workback logic: {e}")
        print(f"This is a BUG: The function cannot handle Unicode in original PATH_INFO")
        return True
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        return False
        
    return False

def test_direct_workback_simulation():
    """Directly test the problematic workback encoding"""
    
    # Simulate the workback process with Unicode
    script_name = ''
    path_info = '/Ā/test'  # Ā cannot be encoded to latin-1
    
    print(f"\nDirect workback simulation:")
    print(f"Original PATH_INFO: {repr(path_info)}")
    
    # Line 293: split the path
    workback = (script_name + path_info).split('/')
    print(f"After split: {workback}")
    
    # Simulate the workback loop (lines 295-301)
    tmp = []
    subpath = ['test']
    
    while workback:
        if tmp == subpath:
            break
        el = workback.pop()
        print(f"\nProcessing element: {repr(el)}")
        
        if el:
            try:
                # Line 301: text_(bytes_(el, 'latin-1'), 'utf-8')
                # First encode to latin-1
                latin1_bytes = el.encode('latin-1')
                print(f"  Encoded to latin-1: {latin1_bytes.hex()}")
                
                # Then decode as UTF-8
                utf8_str = latin1_bytes.decode('utf-8')
                print(f"  Decoded as UTF-8: {repr(utf8_str)}")
                
                tmp.insert(0, utf8_str)
                
            except UnicodeEncodeError as e:
                print(f"  ✗ Cannot encode {repr(el)} to latin-1: {e}")
                print(f"  This is the BUG!")
                return True
            except UnicodeDecodeError as e:
                print(f"  ✗ Cannot decode as UTF-8: {e}")
                return False
    
    print(f"\nFinal tmp: {tmp}")
    return False

def test_euro_in_path():
    """Test with Euro sign in original path"""
    request = Mock()
    request.subpath = ['page']
    request.environ = {
        'SCRIPT_NAME': '/app',
        'PATH_INFO': '/€/page'  # Euro sign U+20AC
    }
    
    new_request = Mock()
    new_request.environ = {}
    new_request.get_response = Mock(return_value="response")
    request.copy = Mock(return_value=new_request)
    
    app = Mock()
    
    print(f"\n\nTesting with Euro sign in PATH_INFO:")
    print(f"Original PATH_INFO: {repr(request.environ['PATH_INFO'])}")
    
    try:
        result = call_app_with_subpath_as_path_info(request, app)
        print("Call succeeded")
        print(f"New SCRIPT_NAME: {repr(new_request.environ.get('SCRIPT_NAME', ''))}")
        print(f"New PATH_INFO: {repr(new_request.environ.get('PATH_INFO', ''))}")
    except UnicodeEncodeError as e:
        print(f"✗ UnicodeEncodeError: {e}")
        print("BUG CONFIRMED: Cannot handle non-latin-1 characters in original PATH_INFO")
        return True
    except Exception as e:
        print(f"Other error: {e}")
        
    return False

if __name__ == "__main__":
    bug_found = False
    
    if test_direct_workback_simulation():
        bug_found = True
        
    if test_workback_with_unicode():
        bug_found = True
        
    if test_euro_in_path():
        bug_found = True
        
    if bug_found:
        print("\n\n🐛 BUG FOUND: The workback logic in call_app_with_subpath_as_path_info")
        print("cannot handle non-latin-1 characters in the original PATH_INFO!")
    else:
        print("\n\nNo bugs found in these tests")