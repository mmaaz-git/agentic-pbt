#!/usr/bin/env python3
"""Advanced property-based tests for fixit.engine module."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fixit_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, HealthCheck
import libcst as cst
from libcst import parse_module, Module, CSTNode
from libcst.metadata import CodeRange, CodePosition
from pathlib import Path

from fixit.engine import LintRunner, diff_violation
from fixit.ftypes import LintViolation, FileContent, Config
from fixit.rule import LintRule


@given(st.text(alphabet="abcdefghijklmnopqrstuvwxyz_0123456789", min_size=1, max_size=20))
@settings(max_examples=1000)
def test_replacement_actually_replaces(var_name):
    """
    Property: When applying a replacement, the specified node should be replaced.
    
    Evidence: ReplacementTransformer replaces nodes in the replacements dict.
    """
    # Ensure valid variable name
    if not var_name[0].isalpha() and var_name[0] != '_':
        var_name = 'x' + var_name
    
    # Create simple code with a variable assignment
    code = f"{var_name} = 1"
    content = code.encode('utf-8')
    runner = LintRunner(path=Path("test.py"), source=content)
    
    # Find the assignment node
    for node in runner.module.walk():
        if isinstance(node, cst.SimpleStatementLine):
            # Create a replacement
            new_node = cst.SimpleStatementLine(body=[cst.Pass()])
            
            violation = LintViolation(
                rule_name="TestRule",
                range=CodeRange(
                    start=CodePosition(line=1, column=0),
                    end=CodePosition(line=1, column=len(code))
                ),
                message="Replace with pass",
                node=node,
                replacement=new_node
            )
            
            # Apply the replacement
            result = runner.apply_replacements([violation])
            
            # The result should be "pass"
            assert result.code.strip() == "pass"
            break


@given(st.lists(st.text(alphabet="abcdefg", min_size=1, max_size=5), min_size=2, max_size=10))
@settings(max_examples=500)
def test_multiple_replacements_all_applied(var_names):
    """
    Property: When applying multiple replacements, all should be applied.
    
    Evidence: apply_replacements processes all violations with replacements.
    """
    # Ensure unique and valid variable names
    var_names = list(set(var_names))
    if len(var_names) < 2:
        assume(False)
    
    # Create code with multiple statements
    lines = [f"var_{name} = {i}" for i, name in enumerate(var_names)]
    code = "\n".join(lines)
    content = code.encode('utf-8')
    runner = LintRunner(path=Path("test.py"), source=content)
    
    violations = []
    statement_count = 0
    
    # Create replacements for each statement
    for node in runner.module.walk():
        if isinstance(node, cst.SimpleStatementLine):
            statement_count += 1
            # Replace each assignment with pass
            new_node = cst.SimpleStatementLine(body=[cst.Pass()])
            
            violation = LintViolation(
                rule_name="TestRule",
                range=CodeRange(
                    start=CodePosition(line=statement_count, column=0),
                    end=CodePosition(line=statement_count, column=10)
                ),
                message=f"Replace statement {statement_count}",
                node=node,
                replacement=new_node
            )
            violations.append(violation)
    
    if violations:
        # Apply all replacements
        result = runner.apply_replacements(violations)
        
        # All lines should be "pass"
        result_lines = result.code.strip().split('\n')
        assert all(line.strip() == "pass" for line in result_lines if line.strip())
        assert len(result_lines) == len(violations)


@given(st.integers(min_value=1, max_value=10))
@settings(max_examples=500)
def test_diff_generation_consistency(num_statements):
    """
    Property: diff_violation should consistently generate diffs for the same change.
    
    Evidence: diff_violation uses unified_diff which should be deterministic.
    """
    # Create code with multiple statements
    code = "\n".join([f"x{i} = {i}" for i in range(num_statements)])
    module = parse_module(code)
    
    # Find first statement
    for node in module.walk():
        if isinstance(node, cst.SimpleStatementLine):
            # Create replacement
            new_node = cst.SimpleStatementLine(body=[cst.Pass()])
            
            violation = LintViolation(
                rule_name="TestRule",
                range=CodeRange(
                    start=CodePosition(line=1, column=0),
                    end=CodePosition(line=1, column=5)
                ),
                message="Test",
                node=node,
                replacement=new_node
            )
            
            # Generate diff multiple times
            diff1 = diff_violation(Path("test.py"), module, violation)
            diff2 = diff_violation(Path("test.py"), module, violation)
            
            # Should be identical
            assert diff1 == diff2
            
            # Should contain the filename
            assert "test.py" in diff1
            break


@given(st.text(alphabet="abcxyz123_", min_size=1, max_size=100))
def test_invalid_python_handled_gracefully(random_text):
    """
    Property: LintRunner should handle invalid Python gracefully.
    
    Evidence: The engine is used to process user code which might be invalid.
    """
    try:
        content = random_text.encode('utf-8')
        runner = LintRunner(path=Path("test.py"), source=content)
        # This should either work or raise a parsing exception
        # but should not crash the interpreter
        assert True
    except Exception as e:
        # Should be a parsing-related exception
        assert "parse" in str(e).lower() or "syntax" in str(e).lower() or "expected" in str(e).lower()


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])