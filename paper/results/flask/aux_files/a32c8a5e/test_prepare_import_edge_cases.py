"""Test more edge cases for prepare_import"""

import os
import sys
import tempfile
import flask.cli

def test_case(description, filename):
    print(f"\n{'='*50}")
    print(f"Test: {description}")
    print(f"Filename: {filename!r}")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_path = os.path.join(tmpdir, filename)
        
        # Create parent dirs if needed
        parent = os.path.dirname(test_path)
        if parent != tmpdir:
            os.makedirs(parent, exist_ok=True)
        
        # Add .py if not present
        if not test_path.endswith('.py'):
            test_path = test_path + '.py'
            
        # Create the file
        try:
            with open(test_path, 'w') as f:
                f.write('# test')
            
            print(f"Created: {test_path}")
            
            # Call prepare_import
            result = flask.cli.prepare_import(test_path)
            print(f"Result: {result!r}")
            
            # Check if .py was stripped
            if result.endswith('.py'):
                print(f"❌ BUG: Result still ends with .py!")
            else:
                print(f"✓ OK: .py extension was stripped")
                
        except Exception as e:
            print(f"Error: {e}")

# Test various edge cases
test_case("Normal file", "module")
test_case("File with dots", "my.module") 
test_case("File ending with slash", "mydir/")
test_case("Just a slash", "/")
test_case("Double slash", "//")
test_case("File named .py", ".py")
test_case("Path with .py in middle", "test.py/module")