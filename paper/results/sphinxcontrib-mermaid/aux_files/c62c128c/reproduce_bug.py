#!/usr/bin/env python3
"""Minimal reproduction of the plistlib control character bug in sphinxcontrib.applehelp."""

import plistlib
import io
import tempfile
import os
import sys

sys.path.insert(0, '/root/hypothesis-llm/envs/sphinxcontrib-mermaid_env/lib/python3.13/site-packages')

def reproduce_bug():
    """Reproduce the bug found in sphinxcontrib.applehelp."""
    
    print("Reproducing plistlib control character bug...")
    print("=" * 60)
    
    # This simulates what happens in AppleHelpBuilder.build_info_plist()
    # when a user configures applehelp_title with control characters
    
    # Create info_plist dict as done in build_info_plist method
    info_plist = {
        'CFBundleDevelopmentRegion': 'en-us',
        'CFBundleIdentifier': 'com.example.test',
        'CFBundleInfoDictionaryVersion': '6.0',
        'CFBundlePackageType': 'BNDL',
        'CFBundleShortVersionString': '1.0',
        'CFBundleSignature': 'hbwr',
        'CFBundleVersion': '1',
        'HPDBookAccessPath': '_access.html',
        'HPDBookIndexPath': 'search.helpindex',
        'HPDBookTitle': 'Test\x1fTitle',  # Title with control character
        'HPDBookType': '3',
        'HPDBookUsesExternalViewer': False,
    }
    
    # Try to dump to plist as done in the actual code
    with tempfile.NamedTemporaryFile(suffix='.plist', delete=False) as f:
        temp_path = f.name
        try:
            plistlib.dump(info_plist, f)
            print("SUCCESS: Plist was written successfully (unexpected!)")
        except ValueError as e:
            print(f"ERROR: {e}")
            print("\nThis error occurs in sphinxcontrib.applehelp when:")
            print("1. A user sets applehelp_title config with control characters")
            print("2. The build_info_plist() method tries to write the Info.plist")
            print("3. plistlib.dump() fails with the above error")
            print("\nThis causes the entire Sphinx build to fail!")
            return True
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    return False

def test_other_control_chars():
    """Test which control characters cause the issue."""
    print("\n" + "=" * 60)
    print("Testing various control characters...")
    
    control_chars = [
        ('\x00', 'NULL'),
        ('\x01', 'SOH'),
        ('\x08', 'BACKSPACE'),
        ('\x0B', 'VERTICAL TAB'),
        ('\x0C', 'FORM FEED'),
        ('\x0E', 'SHIFT OUT'),
        ('\x0F', 'SHIFT IN'),
        ('\x1F', 'UNIT SEPARATOR'),
        ('\x7F', 'DELETE'),
    ]
    
    for char, name in control_chars:
        info_plist = {'TestKey': f'Test{char}Value'}
        buffer = io.BytesIO()
        try:
            plistlib.dump(info_plist, buffer)
            print(f"  {name} ({repr(char)}): OK")
        except ValueError:
            print(f"  {name} ({repr(char)}): FAILS")

if __name__ == '__main__':
    bug_found = reproduce_bug()
    test_other_control_chars()
    
    if bug_found:
        print("\n" + "=" * 60)
        print("BUG CONFIRMED: sphinxcontrib.applehelp fails when config")
        print("values contain control characters!")
        sys.exit(1)