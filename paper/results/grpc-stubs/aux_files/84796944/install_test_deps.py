import subprocess
import sys

venv_python = "/root/hypothesis-llm/envs/grpc-stubs_env/bin/python3"

# Install hypothesis and pytest
result = subprocess.run([venv_python, "-m", "pip", "install", "hypothesis", "pytest"], 
                       capture_output=True, text=True)
print(result.stdout)
if result.returncode != 0:
    print("STDERR:", result.stderr)
    sys.exit(1)
else:
    print("Successfully installed testing dependencies")