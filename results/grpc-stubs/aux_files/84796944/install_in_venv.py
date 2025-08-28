import subprocess
import sys

# Use the virtual environment Python
venv_python = "/root/hypothesis-llm/envs/grpc-stubs_env/bin/python3"

# Install grpcio and grpcio-tools in the virtual environment
result = subprocess.run([venv_python, "-m", "pip", "install", "grpcio", "grpcio-tools", "grpcio-reflection", "grpcio-status"], 
                       capture_output=True, text=True)
print(result.stdout)
if result.returncode != 0:
    print(result.stderr)
    sys.exit(1)
else:
    print("Successfully installed gRPC packages")