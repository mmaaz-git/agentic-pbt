"""Test if subprocess text mode is the issue"""

import subprocess
import sys
import tempfile
import os

# Create a simple script that outputs \r
script_content = """#!/usr/bin/env python3
import sys
sys.stdout.buffer.write(b'\\r')
sys.stdout.flush()
"""

with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
    f.write(script_content)
    temp_script = f.name

try:
    os.chmod(temp_script, 0o755)
    
    # Test 1: Binary mode
    result_binary = subprocess.run([sys.executable, temp_script], capture_output=True)
    print(f"Binary mode stdout: {repr(result_binary.stdout)}")
    
    # Test 2: Text mode  
    result_text = subprocess.run([sys.executable, temp_script], capture_output=True, text=True)
    print(f"Text mode stdout: {repr(result_text.stdout)}")
    
    # Test 3: Text mode with universal_newlines
    result_universal = subprocess.run([sys.executable, temp_script], capture_output=True, universal_newlines=True)
    print(f"Universal newlines stdout: {repr(result_universal.stdout)}")
    
finally:
    os.unlink(temp_script)