import subprocess
import sys

# Install grpcio and grpcio-tools
result = subprocess.run([sys.executable, "-m", "pip", "install", "grpcio", "grpcio-tools"], 
                       capture_output=True, text=True)
print(result.stdout)
if result.returncode != 0:
    print(result.stderr)
    sys.exit(1)