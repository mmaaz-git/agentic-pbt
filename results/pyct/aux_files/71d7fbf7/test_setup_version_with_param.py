#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyct_env/lib/python3.13/site-packages')

import tempfile
import os
from pathlib import Path
from param import version

def test_setup_version():
    """Test what param.version.Version.setup_version returns"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a dummy project structure
        dummy_file = Path(tmpdir) / "setup.py"
        dummy_file.write_text("")
        
        filepath = os.path.abspath(os.path.dirname(str(dummy_file)))
        reponame = "testpackage"
        
        print(f"Testing param.version.Version.setup_version")
        print(f"filepath: {filepath}")
        print(f"reponame: {reponame}")
        print(f"archive_commit: $Format:%h$")
        
        # Call the function
        result = version.Version.setup_version(filepath, reponame, archive_commit="$Format:%h$")
        
        print(f"\nResult: {repr(result)}")
        print(f"Result type: {type(result)}")
        
        # Check if it's the string "None"
        if result == "None":
            print("BUG CONFIRMED: setup_version returns the string 'None' instead of a version!")

if __name__ == "__main__":
    test_setup_version()