#!/root/hypothesis-llm/envs/coremltools_env/bin/python

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/coremltools_env/lib/python3.13/site-packages')

try:
    import coremltools
    import coremltools.converters
    print(f"CoreMLTools version: {coremltools.__version__}")
    print(f"Converters module path: {coremltools.converters.__file__}")
    print("Module imported successfully")
except ImportError as e:
    print(f"Failed to import: {e}")
    sys.exit(1)