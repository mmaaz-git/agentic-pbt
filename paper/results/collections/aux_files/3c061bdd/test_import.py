import sys
print("Python version:", sys.version)
print("Python executable:", sys.executable)

try:
    import flask
    print("Flask imported successfully")
    print("Flask version:", flask.__version__)
except ImportError as e:
    print("Flask not installed:", e)
    print("Installing Flask...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "flask"])