#!/usr/bin/env python3
"""Edge case tests for fixit.engine module."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fixit_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, HealthCheck
import libcst as cst
from libcst import parse_module, Module
from libcst.metadata import CodeRange, CodePosition
from pathlib import Path

from fixit.engine import LintRunner, diff_violation
from fixit.ftypes import LintViolation, Config
from fixit.rule import LintRule


@given(st.sampled_from(["\n", "\r\n", "\r", ""]))
def test_empty_and_whitespace_handling(whitespace):
    """
    Property: LintRunner should handle empty/whitespace files gracefully.
    
    Evidence: Real code often has trailing whitespace or empty files.
    """
    content = whitespace.encode('utf-8')
    runner = LintRunner(path=Path("test.py"), source=content)
    
    # Should be able to apply empty replacements
    result = runner.apply_replacements([])
    assert isinstance(result, Module)
    assert result.code == whitespace


@given(st.text(alphabet="\t \n", min_size=0, max_size=100))
def test_whitespace_only_files(whitespace_text):
    """
    Property: Files with only whitespace should be handled correctly.
    
    Evidence: Empty files are valid Python.
    """
    content = whitespace_text.encode('utf-8')
    runner = LintRunner(path=Path("test.py"), source=content)
    
    # Should handle whitespace-only files
    result = runner.apply_replacements([])
    assert isinstance(result, Module)


@given(st.sampled_from([
    "# -*- coding: utf-8 -*-\nx = 1",
    "#!/usr/bin/env python\nx = 1",
    "# coding: latin-1\nx = 1",
]))
def test_encoding_declarations(code_with_encoding):
    """
    Property: Files with encoding declarations should be handled.
    
    Evidence: Many Python files have encoding declarations.
    """
    content = code_with_encoding.encode('utf-8')
    runner = LintRunner(path=Path("test.py"), source=content)
    
    # Should preserve encoding declarations
    result = runner.apply_replacements([])
    assert isinstance(result, Module)
    # Encoding should be preserved
    assert code_with_encoding in result.code or result.code == code_with_encoding


@given(st.sampled_from([
    b"\xef\xbb\xbfx = 1",  # UTF-8 BOM
    "x = 1".encode('utf-16'),  # Different encoding
]))
def test_byte_order_marks_and_encodings(encoded_content):
    """
    Property: Files with BOMs or different encodings.
    
    Evidence: Real files might have different encodings.
    """
    try:
        runner = LintRunner(path=Path("test.py"), source=encoded_content)
        # If it parses, it should work
        result = runner.apply_replacements([])
        assert isinstance(result, Module)
    except Exception as e:
        # Should be encoding/parsing related
        assert any(word in str(e).lower() for word in ["decode", "encoding", "utf", "parse"])


@given(st.integers(min_value=0, max_value=1000))
def test_deep_nesting(depth):
    """
    Property: Deeply nested code should be handled.
    
    Evidence: Complex code can have deep nesting.
    """
    if depth > 100:
        # Python has recursion limits, be reasonable
        depth = 100
    
    # Create deeply nested if statements
    code = "if True:\n" + "    " * depth + "pass"
    
    try:
        content = code.encode('utf-8')
        runner = LintRunner(path=Path("test.py"), source=content)
        result = runner.apply_replacements([])
        assert isinstance(result, Module)
    except Exception as e:
        # Deep nesting might hit limits
        assert "recursion" in str(e).lower() or "parse" in str(e).lower()


@given(st.sampled_from([
    "x = 1; y = 2",
    "x = 1\ny = 2",
    "x = 1\r\ny = 2",
    "x = 1\ry = 2",
]))
def test_line_ending_preservation(code):
    """
    Property: Different line endings should be preserved.
    
    Evidence: Files use different line ending conventions.
    """
    content = code.encode('utf-8')
    runner = LintRunner(path=Path("test.py"), source=content)
    
    original_module = runner.module
    result = runner.apply_replacements([])
    
    # Line endings should be preserved
    assert result.code == original_module.code


class CollectViolationsRule(LintRule):
    """Test rule that reports on specific nodes."""
    def visit_Assign(self, node):
        self.report(node, "Found assignment")


@given(st.integers(min_value=0, max_value=10))
def test_collect_violations_with_no_rules(num_statements):
    """
    Property: collect_violations with empty rules should yield nothing.
    
    Evidence: No rules means no violations.
    """
    code = "\n".join([f"x{i} = {i}" for i in range(num_statements)])
    content = code.encode('utf-8')
    runner = LintRunner(path=Path("test.py"), source=content)
    
    config = Config(path=Path("test.py"))
    violations = list(runner.collect_violations([], config))
    
    assert len(violations) == 0


@given(st.integers(min_value=1, max_value=10))
def test_timing_hook_called(num_statements):
    """
    Property: Timing hook should be called if provided.
    
    Evidence: Line 114-115 in engine.py shows timings_hook is called.
    """
    code = "\n".join([f"x{i} = {i}" for i in range(num_statements)])
    content = code.encode('utf-8')
    runner = LintRunner(path=Path("test.py"), source=content)
    
    config = Config(path=Path("test.py"))
    
    hook_called = False
    def timing_hook(timings):
        nonlocal hook_called
        hook_called = True
        assert isinstance(timings, dict)
    
    violations = list(runner.collect_violations(
        [CollectViolationsRule()], 
        config, 
        timings_hook=timing_hook
    ))
    
    assert hook_called
    assert len(violations) == num_statements


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])