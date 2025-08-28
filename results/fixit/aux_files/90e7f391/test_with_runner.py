#!/usr/bin/env python3
"""Test rules using the proper LintRunner"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fixit_env/lib/python3.13/site-packages')

from pathlib import Path
from fixit.engine import LintRunner
from fixit.ftypes import Config
from fixit.rules.compare_singleton_primitives_by_is import CompareSingletonPrimitivesByIs

def test_rule_with_runner(code: str, rule_class):
    """Test a rule using LintRunner."""
    print(f"Testing code: {code}")
    
    # Create a fake path
    path = Path.cwd() / "test.py"
    config = Config(path=path)
    
    # Create runner
    runner = LintRunner(path, code.encode())
    
    # Create rule instance
    rule = rule_class()
    
    # Collect violations
    violations = list(runner.collect_violations([rule], config))
    
    print(f"  Violations: {len(violations)}")
    for v in violations:
        print(f"    - {v}")
        if hasattr(v, 'patch') and v.patch:
            print(f"      Patch available")
    
    return violations

print("="*60)
print("Testing INVALID cases from CompareSingletonPrimitivesByIs:")
print("="*60)

rule_class = CompareSingletonPrimitivesByIs

for case in rule_class.INVALID:
    print(f"\\nINVALID case: {case.code}")
    violations = test_rule_with_runner(case.code, rule_class)
    if not violations:
        print("  ⚠️  This INVALID case was NOT detected!")
    else:
        print(f"  ✓ Detected {len(violations)} violation(s)")

print("\\n" + "="*60)
print("Testing VALID cases from CompareSingletonPrimitivesByIs:")
print("="*60)

for case in rule_class.VALID[:5]:  # Test first 5 VALID cases
    print(f"\\nVALID case: {case.code}")
    violations = test_rule_with_runner(case.code, rule_class)
    if violations:
        print(f"  ⚠️  This VALID case was incorrectly flagged!")
    else:
        print(f"  ✓ Correctly passed")