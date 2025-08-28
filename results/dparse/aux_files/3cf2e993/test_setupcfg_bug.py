#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/dparse_env/lib/python3.13/site-packages')

print("Testing SetupCfgParser bug...")
print("=" * 60)

from dparse.dependencies import DependencyFile
from dparse import filetypes

# Test case 1: Basic setup.cfg with install_requires
setup_cfg_content = """
[options]
install_requires = 
    requests>=2.28.0
    numpy==1.24.0
    
[options.extras_require]
dev = 
    pytest>=7.0.0
    black
"""

print("Test 1: Parsing a valid setup.cfg file")
print("Content:")
print(setup_cfg_content)
print("\nAttempting to parse...")

try:
    dep_file = DependencyFile(
        content=setup_cfg_content,
        file_type=filetypes.setup_cfg
    )
    dep_file.parse()
    print(f"✗ UNEXPECTED: Parsing succeeded (should have failed due to bug)")
    print(f"  Found {len(dep_file.dependencies)} dependencies")
    for dep in dep_file.dependencies:
        print(f"    - {dep.name}: {dep.specs}")
except AttributeError as e:
    print(f"✓ BUG CONFIRMED: AttributeError as expected")
    print(f"  Error message: {e}")
    print(f"\n  Analysis: The error occurs because:")
    print(f"    - Line 416: 'section.name' tries to access .name on a string")
    print(f"    - Line 420: 'section.get()' tries to call .get() on a string")
    print(f"    - 'section' is a string from parser.sections(), not an object")
except Exception as e:
    print(f"✗ Unexpected exception: {type(e).__name__}: {e}")

# Test case 2: Empty setup.cfg
print("\n" + "-" * 60)
print("Test 2: Empty setup.cfg (no [options] section)")

empty_cfg = """
[metadata]
name = mypackage
"""

try:
    dep_file = DependencyFile(
        content=empty_cfg,
        file_type=filetypes.setup_cfg
    )
    dep_file.parse()
    print(f"Result: Parsed successfully, found {len(dep_file.dependencies)} dependencies")
except AttributeError as e:
    print(f"✓ BUG TRIGGERED: AttributeError even with no [options] section")
    print(f"  This happens because the bug is in the iteration logic")
except Exception as e:
    print(f"Other exception: {type(e).__name__}: {e}")

print("\n" + "=" * 60)
print("Bug Summary:")
print("  File: dparse/parser.py")
print("  Class: SetupCfgParser")
print("  Lines: 416 and 420")
print("  Issue: Treating string 'section' as an object")
print("  Fix needed: Change 'section.name' to 'section' and 'section.get' to 'parser.get'")
print("=" * 60)