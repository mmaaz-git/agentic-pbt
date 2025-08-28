#!/usr/bin/env python3
"""Investigate the failures found in advanced property tests"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fixit_env/lib/python3.13/site-packages')

import ast
from pathlib import Path
from fixit.engine import LintRunner
from fixit.ftypes import Config


def test_case(code: str, rule_module: str):
    """Test a specific case."""
    print(f"\\nTesting: {repr(code)}")
    print(f"Rule: {rule_module}")
    
    # First check if it's valid Python
    try:
        ast.parse(code)
        print("  ✓ Valid Python syntax")
    except SyntaxError as e:
        print(f"  ✗ Invalid Python: {e}")
        return
    
    # Import the rule
    import importlib
    module = importlib.import_module(f'fixit.rules.{rule_module}')
    rule_class = None
    for name, obj in module.__dict__.items():
        if (isinstance(obj, type) and 
            name != 'LintRule' and 
            hasattr(obj, '__bases__') and 
            any('LintRule' in str(b) for b in obj.__bases__)):
            rule_class = obj
            break
    
    if not rule_class:
        print("  Could not find rule class")
        return
    
    # Run the rule
    path = Path.cwd() / "test.py"
    config = Config(path=path)
    runner = LintRunner(path, code.encode())
    rule = rule_class()
    violations = list(runner.collect_violations([rule], config))
    
    print(f"  Violations: {len(violations)}")
    for v in violations:
        print(f"    Message: {v.message}")
        if v.diff:
            print(f"    Has fix: Yes")


print("="*60)
print("INVESTIGATION OF FAILURES")
print("="*60)

# Test case 1: Lambda with duplicate params
print("\\n1. Lambda with duplicate parameter names:")
test_case("lambda x, x: foo(x, x)", "no_redundant_lambda")

# This should be invalid Python, let's verify
print("\\n  Checking if Python allows duplicate lambda params:")
try:
    eval("lambda x, x: x")
    print("    Python allows it (unexpected!)")
except SyntaxError:
    print("    Python doesn't allow it (expected)")

# Test case 2: Raw f-string without expressions
print("\\n2. Raw f-string without expressions:")
test_case('rf" "', "no_redundant_fstring")
test_case('rf""', "no_redundant_fstring")
test_case('fr""', "no_redundant_fstring")
test_case('f""', "no_redundant_fstring")
test_case('r""', "no_redundant_fstring")

# Test case 3: Comparison without spaces
print("\\n3. Singleton comparison without spaces:")
test_case("x==None", "compare_singleton_primitives_by_is")
test_case("x == None", "compare_singleton_primitives_by_is")
test_case("x!=None", "compare_singleton_primitives_by_is")
test_case("x != None", "compare_singleton_primitives_by_is")

# Additional edge cases
print("\\n4. Other interesting edge cases:")
test_case("None==x", "compare_singleton_primitives_by_is")
test_case("True!=False", "compare_singleton_primitives_by_is")
test_case("x==True==y", "compare_singleton_primitives_by_is")