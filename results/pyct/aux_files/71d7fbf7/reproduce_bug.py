#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyct_env/lib/python3.13/site-packages')

import json
import tempfile
from pathlib import Path
import pyct.build

def test_bug():
    """Minimal reproduction of the bug found in pyct.build.get_setup_version"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Test case 1: Valid JSON with simple value
        reponame = 'testpackage'
        module_dir = Path(tmpdir) / reponame
        module_dir.mkdir()
        
        # Create .version file with valid JSON
        version_file = module_dir / ".version"
        version_data = {"version_string": "1.2.3"}
        version_file.write_text(json.dumps(version_data))
        
        # Create a dummy file to act as root
        dummy_file = Path(tmpdir) / "setup.py"
        dummy_file.write_text("")
        
        # Hide param module to force JSON parsing path
        param_backup = sys.modules.get('param')
        if 'param' in sys.modules:
            del sys.modules['param']
        
        try:
            print(f"Test 1: Testing with version_string='1.2.3'")
            print(f"Version file path: {version_file}")
            print(f"Version file content: {version_file.read_text()}")
            
            result = pyct.build.get_setup_version(str(dummy_file), reponame)
            print(f"Result: {result}")
            print(f"Expected: 1.2.3")
            print(f"Match: {result == '1.2.3'}")
            print()
            
            # Test case 2: Test with "0" as version
            version_data = {"version_string": "0"}
            version_file.write_text(json.dumps(version_data))
            
            print(f"Test 2: Testing with version_string='0'")
            print(f"Version file content: {version_file.read_text()}")
            
            result = pyct.build.get_setup_version(str(dummy_file), reponame)
            print(f"Result: {result}")
            print(f"Result type: {type(result)}")
            print(f"Expected: '0'")
            print(f"Match: {result == '0'}")
            
        finally:
            if param_backup:
                sys.modules['param'] = param_backup

if __name__ == "__main__":
    test_bug()