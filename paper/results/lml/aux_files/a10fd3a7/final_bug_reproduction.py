import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/lml_env/lib/python3.13/site-packages')

from lml.utils import PythonObjectEncoder

encoder = PythonObjectEncoder()

# Minimal reproduction of the bug
result = encoder.default(None)