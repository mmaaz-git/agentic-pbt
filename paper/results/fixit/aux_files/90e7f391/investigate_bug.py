#!/usr/bin/env python3
"""Investigate the bug in compare_singleton_primitives_by_is rule"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fixit_env/lib/python3.13/site-packages')

import libcst as cst
from fixit.rules.compare_singleton_primitives_by_is import CompareSingletonPrimitivesByIs

def test_rule(code: str):
    """Test a rule on a piece of code."""
    print(f"Testing code: {code}")
    
    try:
        # Parse the code
        module = cst.parse_module(code)
        print(f"  Parsed successfully")
        
        # Create rule instance
        rule = CompareSingletonPrimitivesByIs()
        
        # Create wrapper with metadata
        wrapper = cst.MetadataWrapper(module)
        
        # Visit the tree
        rule._violations = []
        wrapper.visit(rule)
        
        violations = rule._violations
        print(f"  Violations found: {len(violations)}")
        
        if violations:
            for v in violations:
                print(f"    - {v.message}")
                if v.replacement:
                    fixed = module.visit(v.replacement)
                    print(f"      Replacement: {fixed.code.strip()}")
        
        return violations
        
    except Exception as e:
        print(f"  Error: {e}")
        import traceback
        traceback.print_exc()
        return []

print("="*60)
print("Testing INVALID cases from the rule definition:")
print("="*60)

# Test the specific failing case
test_rule("x != True")

print("\\n" + "="*60)
print("Testing with explicit module structure:")
print("="*60)

# Try with more complete code structure
test_rule("""
x != True
""".strip())

print("\\n" + "="*60)
print("Let's check what the rule's INVALID cases actually are:")
print("="*60)

for case in CompareSingletonPrimitivesByIs.INVALID:
    print(f"\\nINVALID case: {case.code}")
    violations = test_rule(case.code)
    if not violations:
        print("  ⚠️  This INVALID case was NOT detected!")