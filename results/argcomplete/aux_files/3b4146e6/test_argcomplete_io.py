import sys
import io
import os
import resource
from hypothesis import given, strategies as st, settings
import argcomplete.io


@given(st.text())
def test_mute_stdout_restores_original(text):
    """Property: mute_stdout() should always restore the original stdout"""
    original_stdout = sys.stdout
    
    with argcomplete.io.mute_stdout():
        sys.stdout.write(text)  # This should go to /dev/null
    
    # After the context manager, stdout should be restored
    assert sys.stdout is original_stdout


@given(st.text())
def test_mute_stderr_restores_original(text):
    """Property: mute_stderr() should always restore the original stderr"""
    original_stderr = sys.stderr
    
    with argcomplete.io.mute_stderr():
        sys.stderr.write(text)  # This should go to /dev/null
    
    # After the context manager, stderr should be restored
    assert sys.stderr is original_stderr


@given(st.text(min_size=1))
def test_mute_stdout_actually_mutes(text):
    """Property: When muted, stdout should not capture any output"""
    captured = io.StringIO()
    original_stdout = sys.stdout
    sys.stdout = captured
    
    try:
        with argcomplete.io.mute_stdout():
            print(text)  # This should be muted
        
        # Switch back to capture
        sys.stdout = captured
        print("after_mute")
        
        # Only "after_mute" should be in the output
        output = captured.getvalue()
        assert text not in output
        assert "after_mute" in output
    finally:
        sys.stdout = original_stdout


@given(st.text(min_size=1))
def test_mute_stderr_actually_mutes(text):
    """Property: When muted, stderr should not capture any output"""
    captured = io.StringIO()
    original_stderr = sys.stderr
    sys.stderr = captured
    
    try:
        with argcomplete.io.mute_stderr():
            print(text, file=sys.stderr)  # This should be muted
        
        # Switch back to capture
        sys.stderr = captured
        print("after_mute", file=sys.stderr)
        
        # Only "after_mute" should be in the output
        output = captured.getvalue()
        assert text not in output
        assert "after_mute" in output
    finally:
        sys.stderr = original_stderr


@given(st.integers(min_value=1, max_value=100))
@settings(max_examples=50)
def test_mute_stdout_file_descriptor_leak(n_iterations):
    """Property: Repeated use of mute_stdout should not leak file descriptors"""
    # Get initial file descriptor count
    soft_limit, hard_limit = resource.getrlimit(resource.RLIMIT_NOFILE)
    initial_fds = len(os.listdir('/proc/self/fd'))
    
    # Use mute_stdout multiple times
    for _ in range(n_iterations):
        with argcomplete.io.mute_stdout():
            print("test")
    
    # Check file descriptor count after
    final_fds = len(os.listdir('/proc/self/fd'))
    
    # There should be no significant increase in file descriptors
    # Allow for some variance but not a leak proportional to iterations
    assert final_fds - initial_fds < 10, f"File descriptor leak detected: {initial_fds} -> {final_fds} after {n_iterations} iterations"


@given(st.integers(min_value=1, max_value=100))
@settings(max_examples=50)
def test_mute_stderr_file_descriptor_leak(n_iterations):
    """Property: Repeated use of mute_stderr should not leak file descriptors"""
    # Get initial file descriptor count
    initial_fds = len(os.listdir('/proc/self/fd'))
    
    # Use mute_stderr multiple times
    for _ in range(n_iterations):
        with argcomplete.io.mute_stderr():
            print("test", file=sys.stderr)
    
    # Check file descriptor count after
    final_fds = len(os.listdir('/proc/self/fd'))
    
    # There should be no significant increase in file descriptors
    assert final_fds - initial_fds < 10, f"File descriptor leak detected: {initial_fds} -> {final_fds} after {n_iterations} iterations"


@given(st.lists(st.text()))
def test_warn_prints_to_debug_stream(messages):
    """Property: warn() should print all messages to debug_stream (stderr by default)"""
    # Capture stderr
    captured = io.StringIO()
    original_debug_stream = argcomplete.io.debug_stream
    argcomplete.io.debug_stream = captured
    
    try:
        # Call warn with messages
        if messages:
            argcomplete.io.warn(*messages)
            output = captured.getvalue()
            
            # Should have two newlines (one empty, one with content)
            lines = output.split('\n')
            assert len(lines) >= 2
            
            # All messages should be in the output
            message_line = ' '.join(messages)
            assert message_line in output
    finally:
        argcomplete.io.debug_stream = original_debug_stream


@given(st.lists(st.text()))
def test_debug_respects_debug_flag(messages):
    """Property: debug() should only print when _DEBUG is True"""
    captured = io.StringIO()
    original_debug_stream = argcomplete.io.debug_stream
    original_debug = argcomplete.io._DEBUG
    argcomplete.io.debug_stream = captured
    
    try:
        # Test with _DEBUG = False
        argcomplete.io._DEBUG = False
        if messages:
            argcomplete.io.debug(*messages)
        assert captured.getvalue() == ""
        
        # Test with _DEBUG = True
        captured.truncate(0)
        captured.seek(0)
        argcomplete.io._DEBUG = True
        if messages:
            argcomplete.io.debug(*messages)
            output = captured.getvalue()
            message_line = ' '.join(messages)
            assert message_line in output
    finally:
        argcomplete.io.debug_stream = original_debug_stream
        argcomplete.io._DEBUG = original_debug


@given(st.text())
def test_nested_mute_contexts(text):
    """Property: Nested muting contexts should work correctly"""
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    
    with argcomplete.io.mute_stdout():
        with argcomplete.io.mute_stderr():
            # Both should be muted
            print(text)
            print(text, file=sys.stderr)
        # Only stdout should be muted here
        assert sys.stderr is original_stderr
    
    # Both should be restored
    assert sys.stdout is original_stdout
    assert sys.stderr is original_stderr