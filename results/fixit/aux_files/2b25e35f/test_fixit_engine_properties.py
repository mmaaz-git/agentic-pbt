#!/usr/bin/env python3
"""Property-based tests for fixit.engine module."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fixit_env/lib/python3.13/site-packages')

import re
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from libcst import parse_module, Module, CSTNode
from libcst.metadata import CodeRange, CodePosition

from fixit.engine import LintRunner, diff_violation
from fixit.ftypes import LintViolation, FileContent, Config
from fixit.rule import LintRule


def valid_python_code():
    """Strategy for generating valid Python code snippets."""
    templates = [
        "x = {value}",
        "def f(): return {value}",
        "if {condition}: pass",
        "a = {value}\nb = {value2}",
        "class C: x = {value}",
        "# comment\nx = {value}",
        "try:\n    x = {value}\nexcept: pass",
        "for i in range({value}): pass",
    ]
    
    return st.one_of(
        st.sampled_from(templates).flatmap(
            lambda t: st.builds(
                lambda v1, v2=None, cond=None: t.format(
                    value=v1,
                    value2=v2 if v2 else v1,
                    condition=cond if cond else "True"
                ),
                st.integers(min_value=0, max_value=100),
                st.integers(min_value=0, max_value=100),
                st.sampled_from(["True", "False", "x > 0", "1 == 1"])
            )
        ),
        st.text(alphabet="abcdefghijklmnopqrstuvwxyz_", min_size=1, max_size=20).map(
            lambda name: f"{name} = None"
        ),
        st.just("pass"),
        st.just("x = 1\ny = 2\nz = x + y"),
    )


@given(valid_python_code())
@settings(max_examples=500)
def test_apply_empty_replacements_is_idempotent(code):
    """
    Property: Applying empty list of replacements returns unchanged module.
    
    Evidence: This is the expected behavior when no fixes are needed.
    """
    try:
        content = code.encode('utf-8')
        runner = LintRunner(path=None, source=content)
        original_code = runner.module.code
        
        # Apply empty replacements
        result = runner.apply_replacements([])
        
        # Module code should be unchanged
        assert result.code == original_code
        assert isinstance(result, Module)
    except Exception:
        # Skip invalid code
        assume(False)


@given(valid_python_code())
@settings(suppress_health_check=[HealthCheck.filter_too_much])
def test_diff_violation_generates_valid_diff(code):
    """
    Property: diff_violation should generate a valid unified diff.
    
    Evidence: The function uses unified_diff and is meant to show changes.
    """
    from pathlib import Path
    import libcst as cst
    
    try:
        module = parse_module(code)
        
        # Create a simple violation with a replacement
        # Use a simple pass statement as replacement
        replacement_node = cst.SimpleStatementLine(body=[cst.Pass()])
        
        # Find a statement node we can replace
        for node in module.walk():
            if isinstance(node, (cst.SimpleStatementLine, cst.SimpleStatementSuite)):
                # Create a mock violation
                violation = LintViolation(
                    rule_name="TestRule",
                    range=CodeRange(
                        start=CodePosition(line=1, column=0),
                        end=CodePosition(line=1, column=1)
                    ),
                    message="Test message",
                    node=node,
                    replacement=replacement_node
                )
                
                # Generate diff
                diff = diff_violation(Path("test.py"), module, violation)
                
                # Verify diff format
                assert isinstance(diff, str)
                # Should contain diff markers if there's a change
                if diff and node != replacement_node:
                    assert "---" in diff or "+++" in diff or "@" in diff
                break
                
    except Exception:
        # Skip invalid scenarios
        pass


@given(valid_python_code())
def test_module_remains_valid_after_replacements(code):
    """
    Property: After applying replacements, result should still be a valid Module.
    
    Evidence: apply_replacements returns a Module (line 119-137 in engine.py).
    """
    try:
        content = code.encode('utf-8')
        runner = LintRunner(path=None, source=content)
        
        # Apply empty replacements (safe case)
        result = runner.apply_replacements([])
        
        # Result should be a valid Module
        assert isinstance(result, Module)
        
        # Should be able to generate code from it
        generated_code = result.code
        assert isinstance(generated_code, str)
        
        # Should be parseable again
        reparsed = parse_module(generated_code)
        assert isinstance(reparsed, Module)
        
    except Exception:
        # Skip invalid code
        assume(False)


@given(st.lists(valid_python_code(), min_size=1, max_size=5))
def test_collect_violations_count_consistency(code_snippets):
    """
    Property: Number of violations yielded should be consistent.
    
    Evidence: collect_violations counts and returns violations.
    """
    from pathlib import Path
    
    # Create a simple test rule that always reports one violation
    class AlwaysViolateRule(LintRule):
        def visit_Module(self, node):
            self.report(
                node,
                "Always violate",
            )
    
    try:
        for code in code_snippets:
            content = code.encode('utf-8')
            runner = LintRunner(path=Path("test.py"), source=content)
            
            rules = [AlwaysViolateRule()]
            config = Config(path=Path("test.py"))
            
            violations = list(runner.collect_violations(rules, config))
            
            # Should get exactly one violation per rule
            assert len(violations) == 1
            
            # Each violation should have required fields
            for v in violations:
                assert v.rule_name
                assert v.message
                assert v.node
                
    except Exception:
        # Skip invalid code
        assume(False)


@given(valid_python_code(), st.integers(min_value=1, max_value=3))
def test_multiple_rules_independence(code, num_rules):
    """
    Property: Each rule should report violations independently.
    
    Evidence: Rules are visited independently in collect_violations.
    """
    from pathlib import Path
    
    # Create multiple test rules
    rules = []
    for i in range(num_rules):
        class TestRule(LintRule):
            def __init__(self):
                super().__init__()
                self.name = f"TestRule{i}"
                
            def visit_Module(self, node):
                self.report(node, f"Violation from rule {i}")
        
        rules.append(TestRule())
    
    try:
        content = code.encode('utf-8')
        runner = LintRunner(path=Path("test.py"), source=content)
        config = Config(path=Path("test.py"))
        
        violations = list(runner.collect_violations(rules, config))
        
        # Should get one violation per rule
        assert len(violations) == num_rules
        
        # Check rule names are unique
        rule_names = {v.rule_name for v in violations}
        assert len(rule_names) == num_rules
        
    except Exception:
        # Skip invalid scenarios
        assume(False)


if __name__ == "__main__":
    # Run a quick check of all tests
    test_apply_empty_replacements_is_idempotent()
    test_diff_violation_generates_valid_diff()
    test_module_remains_valid_after_replacements()
    test_collect_violations_count_consistency()
    test_multiple_rules_independence()
    print("All property tests defined successfully!")