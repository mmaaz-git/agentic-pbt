"""Force the workback logic to process Unicode characters"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

from unittest.mock import Mock
from pyramid.request import call_app_with_subpath_as_path_info

def test_unicode_in_subpath_matches_path():
    """Test when Unicode in subpath needs to be matched against path"""
    
    # The workback logic tries to match subpath elements with path components
    # If the subpath contains Unicode that matches path components,
    # the workback needs to process those Unicode characters
    
    request = Mock()
    # Subpath with Unicode - these need to be matched in workback
    request.subpath = ['€', 'test']  # Euro sign that can't encode to latin-1
    request.environ = {
        'SCRIPT_NAME': '/app',
        'PATH_INFO': '/€/test'  # Same Unicode in path
    }
    
    new_request = Mock()
    new_request.environ = {}
    new_request.get_response = Mock(return_value="response")
    request.copy = Mock(return_value=new_request)
    
    app = Mock()
    
    print("Test: Unicode in subpath that needs workback matching")
    print(f"Original SCRIPT_NAME: {repr(request.environ['SCRIPT_NAME'])}")
    print(f"Original PATH_INFO: {repr(request.environ['PATH_INFO'])}")
    print(f"Subpath: {request.subpath}")
    
    try:
        result = call_app_with_subpath_as_path_info(request, app)
        
        print(f"\nNew SCRIPT_NAME: {repr(new_request.environ.get('SCRIPT_NAME', ''))}")
        print(f"New PATH_INFO: {repr(new_request.environ.get('PATH_INFO', ''))}")
        
        # The new PATH_INFO should be the subpath encoded properly
        path_info = new_request.environ.get('PATH_INFO', '')
        print(f"\nPATH_INFO details: {path_info}")
        
    except UnicodeEncodeError as e:
        print(f"\n✗ BUG FOUND: UnicodeEncodeError in workback: {e}")
        return True
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        
    return False

def test_emoji_in_subpath():
    """Test with emoji that definitely can't be in latin-1"""
    
    request = Mock()
    request.subpath = ['🦄', 'page']  # Emoji U+1F984
    request.environ = {
        'SCRIPT_NAME': '',
        'PATH_INFO': '/path/🦄/page'
    }
    
    new_request = Mock()
    new_request.environ = {}
    new_request.get_response = Mock(return_value="response")
    request.copy = Mock(return_value=new_request)
    
    app = Mock()
    
    print("\n\nTest: Emoji in subpath")
    print(f"Original PATH_INFO: {repr(request.environ['PATH_INFO'])}")
    print(f"Subpath: {request.subpath}")
    
    try:
        result = call_app_with_subpath_as_path_info(request, app)
        
        print(f"New SCRIPT_NAME: {repr(new_request.environ.get('SCRIPT_NAME', ''))}")
        print(f"New PATH_INFO: {repr(new_request.environ.get('PATH_INFO', ''))}")
        
    except UnicodeEncodeError as e:
        print(f"\n✗ BUG FOUND: {e}")
        return True
    except Exception as e:
        print(f"Error: {e}")
        
    return False

def test_exact_workback_scenario():
    """Create exact scenario where workback must process Unicode"""
    
    # To force workback to process Unicode:
    # - PATH_INFO must contain the Unicode character
    # - Subpath must match part of the path after the Unicode
    
    request = Mock()
    request.subpath = ['sub', 'path']  # ASCII subpath
    request.environ = {
        'SCRIPT_NAME': '',
        'PATH_INFO': '/prefix/Ā/sub/path'  # Unicode before subpath match
    }
    
    new_request = Mock()
    new_request.environ = {}
    new_request.get_response = Mock(return_value="response")
    request.copy = Mock(return_value=new_request)
    
    app = Mock()
    
    print("\n\nTest: Force workback through Unicode")
    print(f"PATH_INFO: {repr(request.environ['PATH_INFO'])}")
    print(f"Subpath: {request.subpath}")
    print("Workback must process 'Ā' to find where subpath starts")
    
    try:
        result = call_app_with_subpath_as_path_info(request, app)
        
        script_name = new_request.environ.get('SCRIPT_NAME', '')
        path_info = new_request.environ.get('PATH_INFO', '')
        
        print(f"\nResult:")
        print(f"  SCRIPT_NAME: {repr(script_name)}")
        print(f"  PATH_INFO: {repr(path_info)}")
        
        # Script name should be /prefix/Ā if it worked
        if 'Ā' in script_name:
            print("Unicode character preserved in SCRIPT_NAME")
        
    except UnicodeEncodeError as e:
        print(f"\n✗ BUG CONFIRMED: {e}")
        print("The workback cannot process paths with non-latin-1 characters!")
        return True
    except Exception as e:
        print(f"Other error: {e}")
        
    return False

if __name__ == "__main__":
    bugs = []
    
    if test_unicode_in_subpath_matches_path():
        bugs.append("Unicode in subpath matching")
        
    if test_emoji_in_subpath():
        bugs.append("Emoji in subpath")
        
    if test_exact_workback_scenario():
        bugs.append("Workback through Unicode")
        
    if bugs:
        print(f"\n\n🐛 BUGS FOUND in: {', '.join(bugs)}")
    else:
        print("\n\nNo bugs found")