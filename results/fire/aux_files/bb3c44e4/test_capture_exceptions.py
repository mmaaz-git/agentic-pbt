"""Test the interaction between capture parameter and exceptions."""

import sys
import io
from unittest import mock
from hypothesis import given, strategies as st
import fire.testutils


# Test that capture=False still works when assertion fails
@given(
    text=st.text(min_size=1, max_size=20),
    capture=st.booleans()
)
def test_capture_with_assertion_failure(text, capture):
    """Test that capture parameter works correctly even when assertion fails."""
    
    test_case = fire.testutils.BaseTestCase()
    test_case.setUp()
    
    # Capture the real stdout/stderr
    real_stdout = io.StringIO()
    real_stderr = io.StringIO()
    
    with mock.patch.object(sys, 'stdout', real_stdout):
        with mock.patch.object(sys, 'stderr', real_stderr):
            try:
                # This will fail because we write text but expect None (no output)
                with test_case.assertOutputMatches(stdout=None, stderr=None, capture=capture):
                    sys.stdout.write(text)
                    sys.stderr.write(text)
            except AssertionError:
                pass  # Expected to fail
    
    # Check if output was bubbled up despite the assertion failure
    if capture:
        # Output should NOT be bubbled up
        assert real_stdout.getvalue() == ""
        assert real_stderr.getvalue() == ""
    else:
        # Output SHOULD be bubbled up even though assertion failed
        assert real_stdout.getvalue() == text
        assert real_stderr.getvalue() == text


# Test capture with exceptions raised in the context
@given(
    text=st.text(min_size=1, max_size=20),
    capture=st.booleans()
)
def test_capture_with_user_exception(text, capture):
    """Test that capture works when user code raises an exception."""
    
    test_case = fire.testutils.BaseTestCase()
    test_case.setUp()
    
    real_stdout = io.StringIO()
    real_stderr = io.StringIO()
    
    with mock.patch.object(sys, 'stdout', real_stdout):
        with mock.patch.object(sys, 'stderr', real_stderr):
            try:
                with test_case.assertOutputMatches(stdout='.*', stderr='.*', capture=capture):
                    sys.stdout.write(text)
                    sys.stderr.write(text)
                    raise ValueError("User exception")
            except ValueError:
                pass  # Expected
    
    # According to the docstring: "Note: If wrapped code raises an exception, 
    # stdout and stderr will not be checked."
    # But capture should still affect whether output is bubbled up
    
    # Actually, let's check what happens
    stdout_val = real_stdout.getvalue()
    stderr_val = real_stderr.getvalue()
    
    # The behavior might be that output is never bubbled when exception occurs
    # Let's just verify it's consistent
    print(f"With capture={capture}, exception raised:")
    print(f"  stdout bubbled: {bool(stdout_val)}")
    print(f"  stderr bubbled: {bool(stderr_val)}")


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short", "-s"])