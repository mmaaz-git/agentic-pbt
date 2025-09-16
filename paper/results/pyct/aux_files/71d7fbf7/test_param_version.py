#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyct_env/lib/python3.13/site-packages')

# First test with param available
print("Testing with param module available:")
try:
    from param import version
    print(f"param.version exists: {version is not None}")
    print(f"param.version type: {type(version)}")
    if hasattr(version, 'Version'):
        print(f"param.version.Version exists: {hasattr(version, 'Version')}")
except ImportError as e:
    print(f"Could not import param.version: {e}")

# Now test what happens when we import param differently
print("\nTesting param module structure:")
try:
    import param
    print(f"param module: {param}")
    print(f"param.version attribute: {getattr(param, 'version', 'NOT FOUND')}")
    if hasattr(param, 'version'):
        print(f"param.version type: {type(param.version)}")
except ImportError as e:
    print(f"Could not import param: {e}")

# Test the actual condition in the code
print("\nTesting the actual condition used in pyct.build:")
try:
    from param import version
except:
    version = None

print(f"version is not None: {version is not None}")
if version is not None:
    print(f"version.Version exists: {hasattr(version, 'Version')}")
    if hasattr(version, 'Version'):
        print(f"version.Version.setup_version exists: {hasattr(version.Version, 'setup_version')}")
else:
    print("version is None, would use JSON path")