"""Reproduce prepare_import bug with trailing slash"""

import os
import tempfile
import flask.cli

# Create a temporary directory to test
with tempfile.TemporaryDirectory() as tmpdir:
    # Create a file named "0/.py" (which happens when we append .py to "0/")
    test_dir = os.path.join(tmpdir, "0")
    os.makedirs(test_dir, exist_ok=True)
    
    # The bug occurs when the filename ends with a slash
    test_path = test_dir + "/.py"
    
    print(f"Test path: {test_path}")
    
    # Create the file
    with open(test_path, 'w') as f:
        f.write("# test file")
    
    # Call prepare_import
    result = flask.cli.prepare_import(test_path)
    
    print(f"Result from prepare_import: {result!r}")
    print(f"Result ends with .py: {result.endswith('.py')}")
    
    # The bug is that the result still ends with .py
    # when it should have stripped the extension