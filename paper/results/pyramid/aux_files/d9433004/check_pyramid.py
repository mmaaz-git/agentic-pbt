import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyramid_env/lib/python3.13/site-packages')

try:
    import pyramid.httpexceptions as target_module
    print("Success! Module imported")
    print(f"Module file: {target_module.__file__}")
except ImportError as e:
    print(f"Failed to import: {e}")