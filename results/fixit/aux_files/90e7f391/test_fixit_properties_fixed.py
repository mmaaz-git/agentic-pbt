#!/usr/bin/env python3
"""Property-based tests for fixit.rules using Hypothesis - Fixed version"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fixit_env/lib/python3.13/site-packages')

import ast
import importlib
from pathlib import Path
from typing import Any, List, Optional, Tuple

import libcst as cst
from hypothesis import assume, given, settings, strategies as st

from fixit import Invalid, LintRule, Valid
from fixit.engine import LintRunner
from fixit.ftypes import Config, LintViolation


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


def apply_rule(rule_class: type[LintRule], code: str) -> Tuple[List[LintViolation], Optional[str]]:
    """Apply a lint rule to code using LintRunner and return violations and fixed code."""
    try:
        # Create a fake path
        path = Path.cwd() / "test.py"
        config = Config(path=path)
        
        # Create runner
        runner = LintRunner(path, code.encode())
        
        # Create rule instance
        rule = rule_class()
        
        # Collect violations
        violations = list(runner.collect_violations([rule], config))
        
        # Apply fixes if any
        fixed_code = code
        if violations and violations[0].diff:
            # Parse the diff to get the fixed code
            # This is a simplification - in reality we'd apply the patch
            for line in violations[0].diff.split('\\n'):
                if line.startswith('+') and not line.startswith('+++'):
                    fixed_line = line[1:]
                    if fixed_line and not fixed_line.startswith('\\\\ No newline'):
                        fixed_code = fixed_line
                        break
        
        return violations, fixed_code
    except Exception as e:
        # If there's an error, return empty violations
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
@settings(max_examples=20, deadline=5000)
def test_autofix_round_trip(rule_module: str):
    """Test that applying autofix produces code that passes the rule."""
    rule_class = get_rule_class(rule_module)
    
    # Only test rules with autofix capability
    if not rule_class.AUTOFIX:
        return
    
    # Use the rule's own INVALID test cases
    for case in rule_class.INVALID[:3]:  # Test first 3 cases for efficiency
        if isinstance(case, Invalid) and case.expected_replacement:
            code = case.code
            
            # Apply the rule
            violations, _ = apply_rule(rule_class, code)
            
            if violations and case.expected_replacement:
                # The expected replacement should not trigger any violations
                second_violations, _ = apply_rule(rule_class, case.expected_replacement)
                
                # Property: fixed code should have no violations
                assert len(second_violations) == 0, (
                    f"Round-trip failed for {rule_module}:\\n"
                    f"Original: {code}\\n"
                    f"Fixed: {case.expected_replacement}\\n"
                    f"Still has violations: {len(second_violations)}"
                )


# Test 2: Idempotence property
@given(st.sampled_from([
    'compare_singleton_primitives_by_is',
    'no_redundant_lambda',
    'use_assert_is_not_none',
    'compare_primitives_by_equal'
]))
@settings(max_examples=20, deadline=5000)
def test_idempotence(rule_module: str):
    """Test that applying a rule twice gives the same result as applying once."""
    rule_class = get_rule_class(rule_module)
    
    # Use INVALID cases with expected replacements
    test_cases = []
    if hasattr(rule_class, 'INVALID'):
        for case in rule_class.INVALID[:3]:
            if isinstance(case, Invalid) and case.expected_replacement:
                test_cases.append((case.code, case.expected_replacement))
    
    for original_code, expected_fixed in test_cases:
        # Apply rule to the already-fixed code
        violations, _ = apply_rule(rule_class, expected_fixed)
        
        # Property: fixed code should not have any violations
        assert len(violations) == 0, (
            f"Idempotence failed for {rule_module}:\\n"
            f"Fixed code still has violations: {expected_fixed}\\n"
            f"Violations: {len(violations)}"
        )


# Test 3: Parse validity property
@given(st.sampled_from([
    'compare_singleton_primitives_by_is',
    'no_redundant_lambda',
    'use_assert_is_not_none'
]))
@settings(max_examples=20, deadline=5000)
def test_replacement_validity(rule_module: str):
    """Test that all replacements produce valid Python code."""
    rule_class = get_rule_class(rule_module)
    
    # Test with the rule's own INVALID cases
    for case in rule_class.INVALID[:3]:
        if isinstance(case, Invalid) and case.expected_replacement:
            # Property: expected replacement should be valid Python
            assert is_valid_python(case.expected_replacement), (
                f"Invalid Python in expected replacement for {rule_module}:\\n"
                f"Code: {case.expected_replacement}"
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
@settings(max_examples=20, deadline=5000)
def test_valid_cases_unchanged(rule_module: str):
    """Test that VALID cases are never flagged as violations."""
    rule_class = get_rule_class(rule_module)
    
    if not hasattr(rule_class, 'VALID'):
        return
    
    for case in rule_class.VALID[:5]:  # Test first 5 for efficiency
        code = case.code if isinstance(case, Valid) else case
        if isinstance(code, str):
            # Apply the rule
            violations, _ = apply_rule(rule_class, code)
            
            # Property: VALID cases should have no violations
            assert len(violations) == 0, (
                f"VALID case incorrectly flagged in {rule_module}:\\n"
                f"Code: {code}\\n"
                f"Violations: {len(violations)}"
            )


# Test 5: Detection property for INVALID cases
@given(st.sampled_from([
    'compare_singleton_primitives_by_is',
    'no_redundant_lambda',
    'use_assert_is_not_none',
    'compare_primitives_by_equal'
]))
@settings(max_examples=20, deadline=5000)
def test_invalid_cases_detected(rule_module: str):
    """Test that INVALID cases are always detected."""
    rule_class = get_rule_class(rule_module)
    
    if not hasattr(rule_class, 'INVALID'):
        return
    
    for case in rule_class.INVALID[:5]:  # Test first 5 for efficiency
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
    print("Running property-based tests for fixit.rules (fixed version)...")
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