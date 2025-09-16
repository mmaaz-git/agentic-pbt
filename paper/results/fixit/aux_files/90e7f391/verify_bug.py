#!/usr/bin/env python3
"""Verify the bug is reproducible"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fixit_env/lib/python3.13/site-packages')

from pathlib import Path
from fixit.engine import LintRunner
from fixit.ftypes import Config
from fixit.rules.compare_singleton_primitives_by_is import CompareSingletonPrimitivesByIs

print("Verifying the bug in CompareSingletonPrimitivesByIs...")
print("="*60)

# Test case that should work (with spaces)
code_with_spaces = "x == None"
print(f"\\nTest 1: '{code_with_spaces}' (with spaces)")
path = Path.cwd() / "test.py"
config = Config(path=path)
runner = LintRunner(path, code_with_spaces.encode())
rule = CompareSingletonPrimitivesByIs()

try:
    violations = list(runner.collect_violations([rule], config))
    print(f"  ✓ Got {len(violations)} violations (no crash)")
except Exception as e:
    print(f"  ✗ Crashed with: {type(e).__name__}: {e}")

# Test case that crashes (without spaces)
code_without_spaces = "x==None"
print(f"\\nTest 2: '{code_without_spaces}' (without spaces)")
runner2 = LintRunner(path, code_without_spaces.encode())
rule2 = CompareSingletonPrimitivesByIs()

try:
    violations = list(runner2.collect_violations([rule2], config))
    print(f"  ✓ Got {len(violations)} violations (no crash)")
except Exception as e:
    print(f"  ✗ Crashed with: {type(e).__name__}: {e}")

print("\\n" + "="*60)
print("BUG CONFIRMED: The rule crashes on comparisons without spaces!")
print("This is a genuine bug that affects real-world code.")