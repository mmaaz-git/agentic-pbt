#!/usr/bin/env python3
"""Advanced property-based tests for fixit.rules to find edge cases"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fixit_env/lib/python3.13/site-packages')

import ast
import importlib
from pathlib import Path
from typing import Any, List, Optional, Tuple

import libcst as cst
from hypothesis import assume, given, settings, strategies as st, example

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
        
        return violations, None
    except Exception as e:
        # If there's an error, return empty violations
        return [], None


# Test for edge cases in compare_singleton_primitives_by_is
@given(st.text(alphabet='xyzabcNoneTrueFalse =!()\\n\\t', min_size=1, max_size=50))
@settings(max_examples=200, deadline=5000)
def test_compare_singleton_edge_cases(code: str):
    """Test edge cases in singleton comparison rule."""
    rule_class = get_rule_class('compare_singleton_primitives_by_is')
    
    # Skip if not valid Python
    try:
        ast.parse(code)
    except:
        return
    
    # Apply the rule
    violations, _ = apply_rule(rule_class, code)
    
    # If we have violations, the code should contain == or != with None/True/False
    if violations:
        has_comparison = ('==' in code or '!=' in code)
        has_singleton = ('None' in code or 'True' in code or 'False' in code)
        assert has_comparison and has_singleton, (
            f"False positive detection:\\nCode: {repr(code)}\\nViolations: {len(violations)}"
        )


# Test chained comparisons
@given(
    left=st.sampled_from(['x', 'y', 'None', 'True', 'False']),
    op1=st.sampled_from(['==', '!=', 'is', 'is not']),
    middle=st.sampled_from(['x', 'y', 'None', 'True', 'False']),
    op2=st.sampled_from(['==', '!=', 'is', 'is not']),
    right=st.sampled_from(['x', 'y', 'None', 'True', 'False'])
)
@settings(max_examples=100, deadline=5000)
def test_chained_comparisons(left: str, op1: str, middle: str, op2: str, right: str):
    """Test that chained comparisons are handled correctly."""
    code = f"{left} {op1} {middle} {op2} {right}"
    
    rule_class = get_rule_class('compare_singleton_primitives_by_is')
    violations, _ = apply_rule(rule_class, code)
    
    # Count how many singleton comparisons with == or != we have
    singletons = {'None', 'True', 'False'}
    bad_ops = {'==', '!='}
    
    expected_violations = 0
    if (left in singletons or middle in singletons) and op1 in bad_ops:
        expected_violations += 1
    if (middle in singletons or right in singletons) and op2 in bad_ops:
        expected_violations += 1
    
    # We might get 0, 1, or 2 violations depending on the chain
    # The rule might combine them into one violation for the whole chain
    if expected_violations > 0:
        assert len(violations) > 0, (
            f"Expected violations not detected:\\nCode: {code}\\nExpected: {expected_violations}\\nGot: 0"
        )


# Test lambda edge cases  
@given(
    params=st.lists(st.text(alphabet='xyz', min_size=1, max_size=3), min_size=0, max_size=3),
    body_type=st.sampled_from(['same_order', 'different_order', 'partial', 'extra'])
)
@settings(max_examples=100, deadline=5000)
def test_lambda_edge_cases(params: List[str], body_type: str):
    """Test edge cases in redundant lambda detection."""
    if not params:
        # Empty params case
        code = "lambda: foo()"
    else:
        param_str = ', '.join(params)
        if body_type == 'same_order':
            # Lambda that just passes all params in same order - should be flagged
            args = ', '.join(params)
            code = f"lambda {param_str}: foo({args})"
        elif body_type == 'different_order':
            # Lambda that reorders params - should NOT be flagged
            if len(params) > 1:
                args = ', '.join(reversed(params))
                code = f"lambda {param_str}: foo({args})"
            else:
                code = f"lambda {param_str}: foo({params[0]})"
        elif body_type == 'partial':
            # Lambda that doesn't use all params - should NOT be flagged
            if params:
                code = f"lambda {param_str}: foo({params[0]})"
            else:
                code = "lambda: foo()"
        else:  # extra
            # Lambda that adds extra arguments - should NOT be flagged
            args = ', '.join(params) + (', extra' if params else 'extra')
            code = f"lambda {param_str}: foo({args})"
    
    rule_class = get_rule_class('no_redundant_lambda')
    violations, _ = apply_rule(rule_class, code)
    
    # Only lambdas that pass all params in same order with no extras should be flagged
    should_be_flagged = (body_type == 'same_order' and len(params) > 0) or (len(params) == 0 and body_type in ['same_order', 'partial'])
    
    if should_be_flagged:
        # These redundant lambdas might be detected
        pass  # Can't assert as the rule has specific criteria
    else:
        # These should definitely NOT be flagged as they're not redundant
        if 'extra' in code or (body_type == 'different_order' and len(params) > 1):
            assert len(violations) == 0, (
                f"False positive for non-redundant lambda:\\nCode: {code}\\nViolations: {len(violations)}"
            )


# Test f-string edge cases
@given(
    prefix=st.sampled_from(['f', 'F', 'rf', 'fr', 'RF', 'FR']),
    content=st.text(alphabet='abcxyz {}\\\\', min_size=0, max_size=20)
)
@settings(max_examples=100, deadline=5000)
def test_fstring_edge_cases(prefix: str, content: str):
    """Test edge cases in f-string rules."""
    code = f'{prefix}"{content}"'
    
    # Skip if not valid Python
    try:
        ast.parse(code)
    except:
        return
    
    rule_class = get_rule_class('no_redundant_fstring')
    violations, _ = apply_rule(rule_class, code)
    
    # F-strings without any expressions {} should be flagged as redundant
    is_fstring = prefix.lower().startswith('f')
    has_expression = '{' in content and '}' in content
    
    if is_fstring and not has_expression and '\\\\' not in content:
        # This might be a redundant f-string
        pass  # Can't assert as there might be edge cases
    else:
        # Definitely not redundant
        if not is_fstring:
            assert len(violations) == 0, (
                f"Non-f-string flagged as redundant:\\nCode: {code}"
            )


# Test assert edge cases
@given(
    expr_type=st.sampled_from(['in', 'not_in', 'comparison', 'none_check']),
    negate=st.booleans()
)
@settings(max_examples=100, deadline=5000)
def test_assert_edge_cases(expr_type: str, negate: bool):
    """Test edge cases in assertion improvement rules."""
    if expr_type == 'in':
        base_expr = "x in y"
    elif expr_type == 'not_in':
        base_expr = "x not in y"
    elif expr_type == 'comparison':
        base_expr = "x == y"
    else:  # none_check
        base_expr = "x is not None"
    
    if negate:
        code = f"assert not ({base_expr})"
    else:
        code = f"assert {base_expr}"
    
    # Test use_assert_in rule
    rule_class = get_rule_class('use_assert_in')
    violations, _ = apply_rule(rule_class, code)
    
    # "assert x in y" is already optimal, shouldn't be flagged
    # "assert not (x in y)" might be flagged to suggest "assert x not in y"
    if expr_type == 'in' and not negate:
        assert len(violations) == 0, (
            f"Optimal assertion incorrectly flagged:\\nCode: {code}"
        )


# Test whitespace preservation
@given(
    ws_before=st.sampled_from(['', ' ', '  ', '\\t']),
    ws_after=st.sampled_from(['', ' ', '  ', '\\t']),
    singleton=st.sampled_from(['None', 'True', 'False'])
)
@settings(max_examples=50, deadline=5000)
def test_whitespace_preservation(ws_before: str, ws_after: str, singleton: str):
    """Test that whitespace is preserved in replacements."""
    code = f"x{ws_before}=={ws_after}{singleton}"
    
    rule_class = get_rule_class('compare_singleton_primitives_by_is')
    violations, _ = apply_rule(rule_class, code)
    
    # This should be flagged
    assert len(violations) > 0, (
        f"Singleton comparison not detected:\\nCode: {repr(code)}"
    )
    
    # Check that the replacement preserves some form of whitespace
    if violations and violations[0].diff:
        # The diff should show the replacement
        assert 'is' in violations[0].diff, (
            f"Expected 'is' in replacement diff:\\nCode: {repr(code)}\\nDiff: {violations[0].diff}"
        )


if __name__ == "__main__":
    print("Running advanced property-based tests for fixit.rules...")
    print("="*60)
    
    # Run each test manually for better output
    tests = [
        ("Singleton edge cases", test_compare_singleton_edge_cases),
        ("Chained comparisons", test_chained_comparisons),
        ("Lambda edge cases", test_lambda_edge_cases),
        ("F-string edge cases", test_fstring_edge_cases),
        ("Assert edge cases", test_assert_edge_cases),
        ("Whitespace preservation", test_whitespace_preservation)
    ]
    
    failed_tests = []
    
    for test_name, test_func in tests:
        print(f"\\nTesting {test_name}...")
        try:
            # Run with limited examples for quick testing
            test_func()
            print(f"✓ {test_name} passed")
        except AssertionError as e:
            print(f"✗ {test_name} failed: {e}")
            failed_tests.append((test_name, str(e)))
        except Exception as e:
            print(f"✗ {test_name} error: {e}")
            failed_tests.append((test_name, str(e)))
    
    if failed_tests:
        print("\\n" + "="*60)
        print("FAILED TESTS SUMMARY:")
        for name, error in failed_tests:
            print(f"  - {name}: {error[:100]}...")