import subprocess

venv_python = "/root/hypothesis-llm/envs/grpc-stubs_env/bin/python3"
result = subprocess.run([venv_python, "explore_stubs.py"], capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)