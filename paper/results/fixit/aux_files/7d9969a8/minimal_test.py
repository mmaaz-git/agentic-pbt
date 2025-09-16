#!/usr/bin/env python3
"""Minimal property test for fixit.api."""

import sys
from pathlib import Path

sys.path.insert(0, "/root/hypothesis-llm/envs/fixit_env/lib/python3.13/site-packages")

from fixit.api import print_result
from fixit.ftypes import Result, LintViolation, CodeRange, CodePosition
from libcst import CSTNode
import io
import contextlib

# Create a simple mock CST node
class MockNode(CSTNode):
    def _visit_and_replace_children(self, visitor):
        return self
    def _codegen_impl(self, state):
        state.add_token("mock")

# Test 1: print_result return value for clean result
print("Test 1: print_result with clean result...")
clean_result = Result(path=Path("test.py"), violation=None, error=None)
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    is_dirty = print_result(clean_result)
assert is_dirty == False, f"Expected False for clean result, got {is_dirty}"
print("✅ Passed")

# Test 2: print_result return value for result with violation
print("\nTest 2: print_result with violation...")
violation = LintViolation(
    rule_name="TestRule",
    range=CodeRange(
        start=CodePosition(1, 0),
        end=CodePosition(1, 10)
    ),
    message="Test violation",
    node=MockNode(),
    replacement=None,
    diff=""
)
dirty_result = Result(path=Path("test.py"), violation=violation, error=None)
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    is_dirty = print_result(dirty_result)
assert is_dirty == True, f"Expected True for result with violation, got {is_dirty}"
print("✅ Passed")

# Test 3: print_result return value for result with error
print("\nTest 3: print_result with error...")
error_result = Result(
    path=Path("test.py"),
    violation=None, 
    error=(Exception("Test error"), "Traceback...")
)
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    is_dirty = print_result(error_result)
assert is_dirty == True, f"Expected True for result with error, got {is_dirty}"
print("✅ Passed")

# Test 4: LintViolation.autofixable property
print("\nTest 4: LintViolation.autofixable property...")
# Without replacement
violation_no_fix = LintViolation(
    rule_name="TestRule",
    range=CodeRange(
        start=CodePosition(1, 0),
        end=CodePosition(1, 10)
    ),
    message="Test",
    node=MockNode(),
    replacement=None,
    diff=""
)
assert violation_no_fix.autofixable == False, "Expected False when replacement is None"

# With replacement
violation_with_fix = LintViolation(
    rule_name="TestRule",
    range=CodeRange(
        start=CodePosition(1, 0),
        end=CodePosition(1, 10)
    ),
    message="Test",
    node=MockNode(),
    replacement=MockNode(),  # Non-None replacement
    diff=""
)
assert violation_with_fix.autofixable == True, "Expected True when replacement is not None"
print("✅ Passed")

print("\n" + "="*50)
print("All basic property tests passed! ✅")