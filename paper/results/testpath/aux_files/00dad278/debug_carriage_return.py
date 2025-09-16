"""Debug why carriage returns are converted to newlines"""

import sys
import tempfile
import os

# Check the output template used by MockCommand
output_template = """\
sys.stdout.write({!r})
sys.stderr.write({!r})
sys.exit({!r})
"""

# Generate the actual code that would be run
stdout_test = '\r'
stderr_test = 'x\ry'
generated_code = output_template.format(stdout_test, stderr_test, 0)
print("Generated code:")
print(generated_code)
print()

# Write it to a temp file and execute it
with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
    f.write(f"#!/usr/bin/env python3\nimport sys\n{generated_code}")
    temp_script = f.name

try:
    os.chmod(temp_script, 0o755)
    
    # Run it and capture output
    import subprocess
    result = subprocess.run([sys.executable, temp_script], capture_output=True, text=True)
    
    print(f"Expected stdout: {repr(stdout_test)}")
    print(f"Actual stdout: {repr(result.stdout)}")
    print()
    print(f"Expected stderr: {repr(stderr_test)}")
    print(f"Actual stderr: {repr(result.stderr)}")
    
finally:
    os.unlink(temp_script)