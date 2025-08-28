#!/usr/bin/env python3
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fixit_env/lib/python3.13/site-packages')

import importlib
import inspect
import libcst as cst
from fixit import LintRule

# List of rule modules with autofix capabilities
rule_modules = [
    'compare_singleton_primitives_by_is',
    'no_redundant_lambda', 
    'replace_union_with_optional',
    'use_fstring',
    'use_assert_in',
    'use_assert_is_not_none',
    'compare_primitives_by_equal',
    'avoid_or_in_except',
    'cls_in_classmethod',
    'no_redundant_fstring'
]

print("Analyzing fixit.rules for testable properties...")
print("="*60)

autofix_rules = []
visitor_rules = []

for rule_name in rule_modules:
    try:
        module = importlib.import_module(f'fixit.rules.{rule_name}')
        
        # Find the main rule class
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, LintRule) and obj != LintRule and not name.startswith('_'):
                print(f"\nRule: {name}")
                
                # Check for AUTOFIX
                if hasattr(obj, 'AUTOFIX'):
                    print(f"  AUTOFIX: {obj.AUTOFIX}")
                    if obj.AUTOFIX:
                        autofix_rules.append((rule_name, name, obj))
                
                # Check for visitor methods
                visitor_methods = [m for m in dir(obj) if m.startswith('visit_') or m.startswith('leave_')]
                if visitor_methods:
                    print(f"  Visitor methods: {visitor_methods[:3]}...")
                    visitor_rules.append((rule_name, name, obj))
                
                # Check for VALID and INVALID test cases
                valid_count = len(getattr(obj, 'VALID', []))
                invalid_count = len(getattr(obj, 'INVALID', []))
                print(f"  Test cases: {valid_count} VALID, {invalid_count} INVALID")
                
                # Check if any INVALID cases have expected_replacement
                invalid_cases = getattr(obj, 'INVALID', [])
                replacements = sum(1 for case in invalid_cases 
                                 if hasattr(case, 'expected_replacement') 
                                 and case.expected_replacement is not None)
                if replacements > 0:
                    print(f"  Cases with replacements: {replacements}")
                
    except Exception as e:
        print(f"  Error analyzing {rule_name}: {e}")

print("\n" + "="*60)
print(f"Found {len(autofix_rules)} rules with AUTOFIX capability")
print(f"Found {len(visitor_rules)} rules with visitor methods")

print("\n" + "="*60)
print("TESTABLE PROPERTIES:")
print("1. Round-trip: For autofix rules, fix(invalid_code) should pass the rule")
print("2. Idempotence: Applying a rule twice = applying once")  
print("3. Parse validity: All replacements should be valid Python")
print("4. Invariant: VALID code should never trigger violations")
print("5. Detection: INVALID code should always trigger violations")