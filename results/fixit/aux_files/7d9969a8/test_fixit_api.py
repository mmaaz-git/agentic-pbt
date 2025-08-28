#!/usr/bin/env python3
"""Property-based tests for fixit.api module."""

import sys
import traceback
from pathlib import Path
from typing import Optional

import hypothesis.strategies as st
from hypothesis import assume, given, settings
from libcst import CSTNode, RemovalSentinel
from libcst.metadata import CodePosition, CodeRange

sys.path.insert(0, "/root/hypothesis-llm/envs/fixit_env/lib/python3.13/site-packages")

from fixit.api import fixit_bytes, print_result
from fixit.ftypes import Config, FileContent, LintViolation, Result


# Strategy for generating valid Paths
@st.composite
def path_strategy(draw):
    segments = draw(st.lists(
        st.text(alphabet=st.characters(blacklist_categories=('Cc', 'Cs'), min_codepoint=33), min_size=1, max_size=20),
        min_size=1,
        max_size=5
    ))
    # Avoid problematic paths
    assume(all(seg not in [".", "..", "-"] for seg in segments))
    return Path("/".join(segments))


# Strategy for generating CodePositions
@st.composite
def code_position_strategy(draw):
    line = draw(st.integers(min_value=1, max_value=10000))
    column = draw(st.integers(min_value=0, max_value=1000))
    return CodePosition(line, column)


# Strategy for generating CodeRanges
@st.composite
def code_range_strategy(draw):
    start = draw(code_position_strategy())
    # End position should be after start
    end_line = draw(st.integers(min_value=start.line, max_value=start.line + 100))
    if end_line == start.line:
        end_column = draw(st.integers(min_value=start.column, max_value=start.column + 100))
    else:
        end_column = draw(st.integers(min_value=0, max_value=1000))
    end = CodePosition(end_line, end_column)
    return CodeRange(start=start, end=end)


# Strategy for generating simple CST nodes (mock)
class MockCSTNode(CSTNode):
    """Minimal mock CST node for testing."""
    def __init__(self):
        super().__init__()
    
    def _visit_and_replace_children(self, visitor):
        return self
    
    def _codegen_impl(self, state):
        state.add_token("mock")


# Strategy for LintViolation
@st.composite
def lint_violation_strategy(draw):
    rule_name = draw(st.text(min_size=1, max_size=50))
    range_ = draw(code_range_strategy())
    message = draw(st.text(min_size=0, max_size=200))
    node = MockCSTNode()
    
    # Test the autofixable property: randomly include replacement or not
    has_replacement = draw(st.booleans())
    if has_replacement:
        # Can be a node or RemovalSentinel
        if draw(st.booleans()):
            replacement = MockCSTNode()
        else:
            replacement = RemovalSentinel.REMOVE
    else:
        replacement = None
    
    diff = draw(st.text(max_size=500))
    
    return LintViolation(
        rule_name=rule_name,
        range=range_,
        message=message,
        node=node,
        replacement=replacement,
        diff=diff
    )


# Strategy for exceptions with traceback
@st.composite
def exception_with_traceback_strategy(draw):
    error_msg = draw(st.text(min_size=1, max_size=100))
    error = Exception(error_msg)
    # Create a fake traceback
    tb = f"Traceback (most recent call last):\n  File 'test.py', line 1\n{error_msg}"
    return (error, tb)


# Strategy for Result objects
@st.composite
def result_strategy(draw):
    path = draw(path_strategy())
    
    # Result can have either violation OR error, but not both
    result_type = draw(st.sampled_from(["clean", "violation", "error"]))
    
    if result_type == "clean":
        return Result(path=path, violation=None, error=None)
    elif result_type == "violation":
        violation = draw(lint_violation_strategy())
        return Result(path=path, violation=violation, error=None)
    else:  # error
        error = draw(exception_with_traceback_strategy())
        return Result(path=path, violation=None, error=error)


# Test 1: print_result returns True for dirty results, False for clean
@given(result_strategy())
def test_print_result_return_value(result):
    """
    Property: print_result returns True if result is "dirty" (has violation or error),
    False if clean.
    
    Based on api.py lines 34-67.
    """
    import io
    import contextlib
    
    # Capture output to avoid printing during tests
    with contextlib.redirect_stdout(io.StringIO()):
        with contextlib.redirect_stderr(io.StringIO()):
            is_dirty = print_result(result, show_diff=False)
    
    # Check the invariant
    has_violation = result.violation is not None
    has_error = result.error is not None
    expected_dirty = has_violation or has_error
    
    assert is_dirty == expected_dirty, \
        f"print_result returned {is_dirty} but expected {expected_dirty} for result with " \
        f"violation={has_violation}, error={has_error}"


# Test 2: LintViolation.autofixable property
@given(lint_violation_strategy())
def test_lint_violation_autofixable(violation):
    """
    Property: LintViolation.autofixable is True iff replacement is not None.
    
    Based on ftypes.py lines 244-248.
    """
    expected_autofixable = violation.replacement is not None
    actual_autofixable = violation.autofixable
    
    assert actual_autofixable == expected_autofixable, \
        f"autofixable={actual_autofixable} but replacement={'present' if violation.replacement else 'None'}"


# Test 3: fixit_bytes always yields at least one Result
@given(
    path=path_strategy(),
    content=st.binary(max_size=1000),
    autofix=st.booleans()
)
@settings(max_examples=100)
def test_fixit_bytes_yields_result(path, content, autofix):
    """
    Property: fixit_bytes always yields at least one Result, even with empty config.
    
    Based on api.py lines 76-122, specifically lines 97 and 111.
    """
    # Create minimal config
    config = Config(path=path, enable=[], disable=[])
    
    generator = fixit_bytes(path, content, config=config, autofix=autofix)
    
    results = []
    try:
        # Collect all yielded results
        value = None
        while True:
            try:
                result = generator.send(value)
                results.append(result)
                value = False  # Don't apply fixes
            except StopIteration as e:
                # Generator completed, get return value
                return_value = e.value
                break
    except Exception as e:
        # Even if there's an error, we should have gotten at least one Result
        pass
    
    assert len(results) >= 1, \
        f"fixit_bytes yielded {len(results)} results, expected at least 1"
    
    # All yielded values should be Result objects
    for r in results:
        assert isinstance(r, Result), f"Expected Result, got {type(r)}"
        assert isinstance(r.path, Path), f"Result.path should be Path, got {type(r.path)}"


# Test 4: Result object invariants
@given(result_strategy())
def test_result_invariants(result):
    """
    Property: Result objects maintain their invariants.
    - Always have a path
    - Can have either violation OR error, but not both
    
    Based on ftypes.py lines 252-259.
    """
    # Must have a path
    assert result.path is not None, "Result must have a path"
    assert isinstance(result.path, Path), f"Result.path must be Path, got {type(result.path)}"
    
    # Cannot have both violation and error
    if result.violation is not None and result.error is not None:
        assert False, "Result cannot have both violation and error"
    
    # If has error, it should be a tuple of (Exception, str)
    if result.error is not None:
        assert isinstance(result.error, tuple), f"error must be tuple, got {type(result.error)}"
        assert len(result.error) == 2, f"error tuple must have 2 elements, got {len(result.error)}"
        assert isinstance(result.error[0], Exception), \
            f"error[0] must be Exception, got {type(result.error[0])}"
        assert isinstance(result.error[1], str), \
            f"error[1] must be str, got {type(result.error[1])}"


# Test 5: Config path resolution
@given(st.text(min_size=1, max_size=100))
def test_config_path_resolution(path_str):
    """
    Property: Config paths are always resolved to absolute paths.
    
    Based on ftypes.py lines 215-217.
    """
    assume("/" not in path_str and "\\" not in path_str)  # Avoid absolute paths
    assume(path_str not in [".", "..", "-"])  # Avoid special paths
    
    relative_path = Path(path_str)
    config = Config(path=relative_path)
    
    # After __post_init__, path should be resolved
    assert config.path.is_absolute(), \
        f"Config.path should be absolute after init, got {config.path}"
    
    # Root should also be resolved
    assert config.root.is_absolute(), \
        f"Config.root should be absolute after init, got {config.root}"


if __name__ == "__main__":
    import pytest
    
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])