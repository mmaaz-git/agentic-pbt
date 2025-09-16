"""Property-based tests for fire.testutils using Hypothesis."""

import os
import sys
import tempfile
import re
from contextlib import contextmanager
from unittest import mock
import io

from hypothesis import given, strategies as st, assume, settings
import fire.testutils


# Test 1: ChangeDirectory round-trip property
@given(st.text(min_size=1).filter(lambda x: '/' not in x and '\\' not in x and '.' not in x))
def test_change_directory_round_trip(dirname):
    """Test that ChangeDirectory always restores the original directory."""
    # Create a temporary directory structure
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create the subdirectory
        subdir = os.path.join(tmpdir, dirname)
        try:
            os.makedirs(subdir, exist_ok=True)
        except (OSError, ValueError):
            assume(False)  # Skip invalid directory names
        
        # Get original directory
        original_dir = os.getcwd()
        
        # Use ChangeDirectory
        with fire.testutils.ChangeDirectory(subdir):
            # We should be in the subdir now
            assert os.getcwd() == os.path.abspath(subdir)
        
        # After exiting, we should be back
        assert os.getcwd() == original_dir


# Test 2: ChangeDirectory exception safety
@given(st.text(min_size=1).filter(lambda x: '/' not in x and '\\' not in x and '.' not in x))
def test_change_directory_exception_safety(dirname):
    """Test that ChangeDirectory restores directory even when exception is raised."""
    with tempfile.TemporaryDirectory() as tmpdir:
        subdir = os.path.join(tmpdir, dirname)
        try:
            os.makedirs(subdir, exist_ok=True)
        except (OSError, ValueError):
            assume(False)
        
        original_dir = os.getcwd()
        
        # Raise an exception inside the context
        try:
            with fire.testutils.ChangeDirectory(subdir):
                assert os.getcwd() == os.path.abspath(subdir)
                raise ValueError("Test exception")
        except ValueError:
            pass  # Expected
        
        # Directory should still be restored
        assert os.getcwd() == original_dir


# Test 3: assertOutputMatches regex matching property
@given(
    stdout_text=st.text(),
    stderr_text=st.text(),
    stdout_pattern=st.one_of(st.none(), st.text(min_size=1)),
    stderr_pattern=st.one_of(st.none(), st.text(min_size=1))
)
def test_assert_output_matches_regex_property(stdout_text, stderr_text, stdout_pattern, stderr_pattern):
    """Test that assertOutputMatches correctly matches regex patterns."""
    
    # Create a test case instance
    test_case = fire.testutils.BaseTestCase()
    test_case.setUp()
    
    # Skip invalid regex patterns
    if stdout_pattern is not None:
        try:
            re.compile(stdout_pattern)
        except re.error:
            assume(False)
    if stderr_pattern is not None:
        try:
            re.compile(stderr_pattern)
        except re.error:
            assume(False)
    
    # Test the regex matching behavior
    try:
        with test_case.assertOutputMatches(stdout=stdout_pattern, stderr=stderr_pattern):
            # Write to stdout and stderr
            sys.stdout.write(stdout_text)
            sys.stderr.write(stderr_text)
        
        # If we get here, the assertion passed
        # Verify the patterns should have matched
        if stdout_pattern is None:
            assert stdout_text == "", f"Expected no stdout but got: {stdout_text!r}"
        else:
            assert re.search(stdout_pattern, stdout_text, re.DOTALL | re.MULTILINE) is not None
        
        if stderr_pattern is None:
            assert stderr_text == "", f"Expected no stderr but got: {stderr_text!r}"
        else:
            assert re.search(stderr_pattern, stderr_text, re.DOTALL | re.MULTILINE) is not None
            
    except AssertionError as e:
        # The assertion failed - verify it should have failed
        error_msg = str(e)
        
        if stdout_pattern is None and stdout_text:
            assert "stdout: Expected no output" in error_msg
        elif stdout_pattern is not None:
            if not re.search(stdout_pattern, stdout_text, re.DOTALL | re.MULTILINE):
                assert "stdout: Expected" in error_msg or "to match" in error_msg
        
        if stderr_pattern is None and stderr_text:
            assert "stderr: Expected no output" in error_msg
        elif stderr_pattern is not None:
            if not re.search(stderr_pattern, stderr_text, re.DOTALL | re.MULTILINE):
                assert "stderr: Expected" in error_msg or "to match" in error_msg


# Test 4: assertOutputMatches capture property
@given(
    text=st.text(min_size=1, max_size=100),
    capture=st.booleans()
)
def test_assert_output_matches_capture_property(text, capture):
    """Test that capture parameter controls whether output is bubbled up."""
    test_case = fire.testutils.BaseTestCase()
    test_case.setUp()
    
    # Capture the real stdout/stderr
    real_stdout = io.StringIO()
    real_stderr = io.StringIO()
    
    with mock.patch.object(sys, 'stdout', real_stdout):
        with mock.patch.object(sys, 'stderr', real_stderr):
            with test_case.assertOutputMatches(stdout='.*', stderr='.*', capture=capture):
                # Write some output inside the context
                sys.stdout.write(text)
                sys.stderr.write(text)
    
    # Check if output was bubbled up
    if capture:
        # Output should NOT be bubbled up
        assert real_stdout.getvalue() == ""
        assert real_stderr.getvalue() == ""
    else:
        # Output SHOULD be bubbled up
        assert real_stdout.getvalue() == text
        assert real_stderr.getvalue() == text


if __name__ == "__main__":
    # Run the tests
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])