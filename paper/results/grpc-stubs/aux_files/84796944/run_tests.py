import subprocess
import sys

venv_python = "/root/hypothesis-llm/envs/grpc-stubs_env/bin/python3"

# Run the tests
result = subprocess.run([venv_python, "-m", "pytest", "test_grpc_stubs.py", "-v", "--tb=short"], 
                       capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)