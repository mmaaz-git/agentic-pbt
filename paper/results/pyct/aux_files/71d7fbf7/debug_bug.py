#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyct_env/lib/python3.13/site-packages')

import json
import tempfile
import os
from pathlib import Path

def debug_get_setup_version():
    """Debug the get_setup_version function step by step"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        reponame = 'testpackage'
        
        # Create the expected file structure
        dummy_file = Path(tmpdir) / "setup.py"
        dummy_file.write_text("")
        
        # Trace through the function logic
        print("Tracing get_setup_version logic:")
        print(f"1. root parameter: {dummy_file}")
        
        filepath = os.path.abspath(os.path.dirname(str(dummy_file)))
        print(f"2. filepath = os.path.abspath(os.path.dirname(root)): {filepath}")
        
        version_file_path = os.path.join(filepath, reponame, '.version')
        print(f"3. version_file_path = os.path.join(filepath, reponame, '.version'): {version_file_path}")
        
        # Create the directory and file
        os.makedirs(os.path.dirname(version_file_path), exist_ok=True)
        version_data = {"version_string": "1.2.3"}
        with open(version_file_path, 'w') as f:
            json.dump(version_data, f)
        
        print(f"4. Created version file with content: {json.dumps(version_data)}")
        
        # Hide param module
        param_backup = sys.modules.get('param')
        if 'param' in sys.modules:
            del sys.modules['param']
        
        try:
            # Now simulate the function's behavior
            print("\n5. param module is not available, so going to else branch")
            print("6. Executing: json.load(open(version_file_path, 'r'))['version_string']")
            
            # Check if file exists
            print(f"7. File exists: {os.path.exists(version_file_path)}")
            
            if os.path.exists(version_file_path):
                with open(version_file_path, 'r') as f:
                    data = json.load(f)
                    print(f"8. Loaded JSON data: {data}")
                    result = data['version_string']
                    print(f"9. Extracted version_string: {result}")
            else:
                print("8. File does not exist!")
                
            # Now actually call the function
            print("\n10. Actually calling pyct.build.get_setup_version:")
            import pyct.build
            actual_result = pyct.build.get_setup_version(str(dummy_file), reponame)
            print(f"11. Actual result: {actual_result}")
            print(f"12. Type of result: {type(actual_result)}")
            
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if param_backup:
                sys.modules['param'] = param_backup

if __name__ == "__main__":
    debug_get_setup_version()