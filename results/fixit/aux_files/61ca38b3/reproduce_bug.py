#!/usr/bin/env python3
"""Reproduce the idempotence bug in FixitRemoveRuleSuffix"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fixit_env/lib/python3.13/site-packages')

from pathlib import Path
from fixit.upgrade.remove_rule_suffix import FixitRemoveRuleSuffix
from fixit.engine import LintRunner
from fixit.ftypes import Config

# Bug 1: Reserved keyword issue
def test_reserved_keyword():
    code = """
from fixit import LintRule

class FalseRule(LintRule):
    pass
"""
    
    path = Path.cwd() / "test.py"
    config = Config(path=path)
    runner = LintRunner(path, code.encode())
    rule = FixitRemoveRuleSuffix()
    
    reports = list(runner.collect_violations([rule], config))
    
    if reports:
        result = runner.apply_replacements(reports).bytes.decode()
        print("Original code:")
        print(code)
        print("\nAfter applying rule:")
        print(result)
        print("\nThis creates invalid Python - 'False' is a reserved keyword!")
        
        # Try to parse the result
        try:
            import libcst as cst
            cst.parse_module(result)
            print("Result parses successfully")
        except Exception as e:
            print(f"Result fails to parse: {e}")

# Bug 2: Non-idempotence issue  
def test_idempotence():
    code = """
from fixit import LintRule

class AAAAARule(LintRule):
    pass
"""
    
    path = Path.cwd() / "test.py"
    config = Config(path=path)
    runner = LintRunner(path, code.encode())
    rule = FixitRemoveRuleSuffix()
    
    reports = list(runner.collect_violations([rule], config))
    print(f"\nFirst run - found {len(reports)} violations")
    
    if reports:
        result = runner.apply_replacements(reports).bytes.decode()
        print("After first application:")
        print(result)
        
        # Apply the rule a second time
        runner2 = LintRunner(path, result.encode())
        reports2 = list(runner2.collect_violations([rule], config))
        print(f"\nSecond run - found {len(reports2)} violations")
        
        if reports2:
            print("Violation details:")
            for r in reports2:
                print(f"  - Message: {r.message}")
                print(f"  - Node value: {runner2.module.code_for_node(r.node)}")
                print(f"  - Replacement: {runner2.module.code_for_node(r.replacement)}")
            
            print("\nBUG: Rule is not idempotent! It still reports violations after being applied.")
            print("The issue is that it's trying to replace 'AAAAARule' even though the code now has 'AAAAA'")

if __name__ == "__main__":
    print("=== Testing Reserved Keyword Bug ===")
    test_reserved_keyword()
    
    print("\n=== Testing Idempotence Bug ===")
    test_idempotence()