#!/usr/bin/env python3
import sys
import io
sys.path.insert(0, '/root/hypothesis-llm/envs/pyct_env/lib/python3.13/site-packages')

import json
import tempfile
import os
from pathlib import Path
import pyct.build

def test_with_stdout_capture():
    """Test if the function is printing instead of returning"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        reponame = 'testpackage'
        
        # Create the expected file structure
        dummy_file = Path(tmpdir) / "setup.py"
        dummy_file.write_text("")
        
        filepath = os.path.abspath(os.path.dirname(str(dummy_file)))
        version_file_path = os.path.join(filepath, reponame, '.version')
        
        # Create the directory and file
        os.makedirs(os.path.dirname(version_file_path), exist_ok=True)
        version_data = {"version_string": "1.2.3"}
        with open(version_file_path, 'w') as f:
            json.dump(version_data, f)
        
        # Hide param module
        param_backup = sys.modules.get('param')
        if 'param' in sys.modules:
            del sys.modules['param']
        
        try:
            # Capture stdout
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()
            
            result = pyct.build.get_setup_version(str(dummy_file), reponame)
            
            # Get what was printed
            stdout_output = sys.stdout.getvalue()
            sys.stdout = old_stdout
            
            print(f"Function returned: {repr(result)}")
            print(f"Function printed to stdout: {repr(stdout_output)}")
            
            # Also check the actual implementation more carefully
            print("\nLet's check line 46 of the implementation:")
            print("The line is: return json.load(open(version_file_path, 'r'))['version_string']")
            print("\nBut wait, there's a print statement on line 45!")
            print("Line 45: print(\"WARNING: param>=1.6.0 unavailable...\")")
            print("\nSo it prints a warning, then returns the version.")
            
        finally:
            sys.stdout = old_stdout
            if param_backup:
                sys.modules['param'] = param_backup

if __name__ == "__main__":
    test_with_stdout_capture()