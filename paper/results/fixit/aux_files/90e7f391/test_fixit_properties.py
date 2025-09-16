#!/usr/bin/env python3
"""Property-based tests for fixit.rules using Hypothesis"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fixit_env/lib/python3.13/site-packages')

import ast
import importlib
from typing import Any, Optional

import libcst as cst
from hypothesis import assume, given, settings, strategies as st
from hypothesis.strategies import SearchStrategy

from fixit import Invalid, LintRule, Valid
from fixit.rule import LintViolation


def get_rule_class(module_name: str) -> type[LintRule]:
    """Get the main rule class from a module."""
    module = importlib.import_module(f'fixit.rules.{module_name}')
    for name, obj in module.__dict__.items():
        if (isinstance(obj, type) and 
            issubclass(obj, LintRule) and 
            obj != LintRule and 
            not name.startswith('_')):
            return obj
    raise ValueError(f"No rule class found in {module_name}")


def apply_rule(rule_class: type[LintRule], code: str) -> tuple[list[LintViolation], Optional[str]]:
    """Apply a lint rule to code and return violations and fixed code."""
    try:
        # Parse the code
        module = cst.parse_module(code)
        
        # Create rule instance and run it
        rule = rule_class()
        wrapper = cst.MetadataWrapper(module)
        
        # Visit the tree
        violations = []
        rule._violations = []
        wrapper.visit(rule)
        violations = rule._violations
        
        # Apply fixes if any
        fixed_code = code
        if violations and violations[0].replacement is not None:
            # Apply the first fix
            fixed_module = module.visit(violations[0].replacement)
            fixed_code = fixed_module.code
        
        return violations, fixed_code
    except Exception:
        # If parsing fails, return empty violations
        return [], None


def is_valid_python(code: str) -> bool:
    """Check if code is valid Python."""
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False


# Strategy for generating Python-like code snippets
@st.composite
def python_snippet(draw: Any) -> str:
    """Generate simple Python code snippets."""
    snippet_type = draw(st.sampled_from([
        'comparison', 'lambda', 'assertion', 'fstring', 'except'
    ]))
    
    if snippet_type == 'comparison':
        left = draw(st.sampled_from(['x', 'y', 'None', 'True', 'False', '1', '"str"']))
        op = draw(st.sampled_from(['==', '!=', 'is', 'is not']))
        right = draw(st.sampled_from(['x', 'y', 'None', 'True', 'False', '2', '"str"']))
        return f"{left} {op} {right}"
    
    elif snippet_type == 'lambda':
        params = draw(st.sampled_from(['', 'x', 'x, y', 'x, y, z']))
        body = draw(st.sampled_from(['x', 'foo()', 'foo(x)', 'x + y', 'None']))
        return f"lambda {params}: {body}" if params else f"lambda: {body}"
    
    elif snippet_type == 'assertion':
        expr = draw(st.sampled_from([
            'x in y', 'x not in y', 'x == y', 'x != None', 
            'x is not None', 'len(x) > 0'
        ]))
        return f"assert {expr}"
    
    elif snippet_type == 'fstring':
        content = draw(st.sampled_from(['x', '{x}', 'hello', '{x + 1}', '']))
        return f'f"{content}"'
    
    else:  # except
        exceptions = draw(st.sampled_from([
            'Exception', 'ValueError', 
            '(ValueError, TypeError)', 
            'ValueError or TypeError'
        ]))
        return f"try:\\n    pass\\nexcept {exceptions}:\\n    pass"


# Test 1: Round-trip property for autofix rules
@given(st.sampled_from([
    'compare_singleton_primitives_by_is',
    'no_redundant_lambda',
    'use_assert_is_not_none',
    'compare_primitives_by_equal',
    'no_redundant_fstring'
]))
@settings(max_examples=50, deadline=2000)
def test_autofix_round_trip(rule_module: str):
    """Test that applying autofix produces code that passes the rule."""
    rule_class = get_rule_class(rule_module)
    
    # Only test rules with autofix capability
    if not rule_class.AUTOFIX:
        return
    
    # Use the rule's own INVALID test cases
    for case in rule_class.INVALID:
        if isinstance(case, Invalid) and case.expected_replacement:
            code = case.code
            
            # Apply the rule
            violations, fixed_code = apply_rule(rule_class, code)
            
            if fixed_code and fixed_code != code:
                # The fixed code should not trigger any violations
                second_violations, _ = apply_rule(rule_class, fixed_code)
                
                # Property: fixed code should have no violations
                assert len(second_violations) == 0, (
                    f"Round-trip failed for {rule_module}:\\n"
                    f"Original: {code}\\n"
                    f"Fixed: {fixed_code}\\n"
                    f"Still has violations: {second_violations}"
                )


# Test 2: Idempotence property
@given(st.sampled_from([
    'compare_singleton_primitives_by_is',
    'no_redundant_lambda',
    'use_assert_is_not_none',
    'compare_primitives_by_equal'
]))
@settings(max_examples=50, deadline=2000)
def test_idempotence(rule_module: str):
    """Test that applying a rule twice gives the same result as applying once."""
    rule_class = get_rule_class(rule_module)
    
    # Use both VALID and INVALID cases
    test_cases = []
    if hasattr(rule_class, 'VALID'):
        test_cases.extend(case.code if isinstance(case, Valid) else case 
                         for case in rule_class.VALID if isinstance(case, (str, Valid)))
    if hasattr(rule_class, 'INVALID'):
        test_cases.extend(case.code if isinstance(case, Invalid) else case 
                         for case in rule_class.INVALID if isinstance(case, (str, Invalid)))
    
    for code in test_cases[:5]:  # Test first 5 cases for efficiency
        # Apply rule once
        violations1, fixed1 = apply_rule(rule_class, code)
        
        if fixed1:
            # Apply rule to the fixed code
            violations2, fixed2 = apply_rule(rule_class, fixed1)
            
            # Property: second application should not change the code
            assert fixed2 == fixed1 or fixed2 is None, (
                f"Idempotence failed for {rule_module}:\\n"
                f"Original: {code}\\n"
                f"After 1st: {fixed1}\\n"
                f"After 2nd: {fixed2}"
            )


# Test 3: Parse validity property
@given(python_snippet())
@settings(max_examples=100, deadline=2000)
def test_replacement_validity(code: str):
    """Test that all replacements produce valid Python code."""
    # Test multiple rules
    rules_to_test = [
        'compare_singleton_primitives_by_is',
        'no_redundant_lambda',
        'use_assert_is_not_none'
    ]
    
    for rule_module in rules_to_test:
        rule_class = get_rule_class(rule_module)
        
        # Apply the rule
        violations, fixed_code = apply_rule(rule_class, code)
        
        if fixed_code and fixed_code != code:
            # Property: fixed code should be valid Python
            assert is_valid_python(fixed_code), (
                f"Invalid Python produced by {rule_module}:\\n"
                f"Original: {code}\\n"
                f"Fixed: {fixed_code}"
            )


# Test 4: Invariant property for VALID cases
@given(st.sampled_from([
    'compare_singleton_primitives_by_is',
    'no_redundant_lambda',
    'use_assert_is_not_none',
    'compare_primitives_by_equal',
    'no_redundant_fstring',
    'use_fstring'
]))
@settings(max_examples=50, deadline=2000)
def test_valid_cases_unchanged(rule_module: str):
    """Test that VALID cases are never flagged as violations."""
    rule_class = get_rule_class(rule_module)
    
    if not hasattr(rule_class, 'VALID'):
        return
    
    for case in rule_class.VALID:
        code = case.code if isinstance(case, Valid) else case
        if isinstance(code, str):
            # Apply the rule
            violations, _ = apply_rule(rule_class, code)
            
            # Property: VALID cases should have no violations
            assert len(violations) == 0, (
                f"VALID case incorrectly flagged in {rule_module}:\\n"
                f"Code: {code}\\n"
                f"Violations: {violations}"
            )


# Test 5: Detection property for INVALID cases
@given(st.sampled_from([
    'compare_singleton_primitives_by_is',
    'no_redundant_lambda',
    'use_assert_is_not_none',
    'compare_primitives_by_equal'
]))
@settings(max_examples=50, deadline=2000)
def test_invalid_cases_detected(rule_module: str):
    """Test that INVALID cases are always detected."""
    rule_class = get_rule_class(rule_module)
    
    if not hasattr(rule_class, 'INVALID'):
        return
    
    for case in rule_class.INVALID:
        code = case.code if isinstance(case, Invalid) else case
        if isinstance(code, str):
            # Apply the rule
            violations, _ = apply_rule(rule_class, code)
            
            # Property: INVALID cases should have violations
            assert len(violations) > 0, (
                f"INVALID case not detected in {rule_module}:\\n"
                f"Code: {code}"
            )


if __name__ == "__main__":
    print("Running property-based tests for fixit.rules...")
    print("="*60)
    
    # Run each test manually for better output
    tests = [
        ("Round-trip", test_autofix_round_trip),
        ("Idempotence", test_idempotence),
        ("Parse validity", test_replacement_validity),
        ("Valid unchanged", test_valid_cases_unchanged),
        ("Invalid detected", test_invalid_cases_detected)
    ]
    
    for test_name, test_func in tests:
        print(f"\\nTesting {test_name} property...")
        try:
            # Run with limited examples for quick testing
            test_func()
            print(f"✓ {test_name} passed")
        except AssertionError as e:
            print(f"✗ {test_name} failed: {e}")
        except Exception as e:
            print(f"✗ {test_name} error: {e}")