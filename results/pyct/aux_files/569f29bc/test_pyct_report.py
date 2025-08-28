#!/usr/bin/env python3
"""Property-based tests for pyct.report module using Hypothesis"""

import sys
import io
import subprocess
from unittest import mock
from hypothesis import given, strategies as st, assume, settings
from pyct.report import report


@given(st.text(min_size=1))
def test_report_does_not_crash_on_arbitrary_package_names(package_name):
    """Test that report() doesn't crash on arbitrary package names"""
    assume('\x00' not in package_name)
    assume('\n' not in package_name)
    assume('\r' not in package_name)
    
    captured_output = io.StringIO()
    sys.stdout = captured_output
    try:
        report(package_name)
    finally:
        sys.stdout = sys.__stdout__
    
    output = captured_output.getvalue()
    assert package_name in output
    assert '=' in output
    assert '#' in output


@given(st.lists(st.text(min_size=1, max_size=50), min_size=1, max_size=10))
def test_report_multiple_packages_produces_multiple_lines(package_names):
    """Test that multiple packages produce multiple lines of output"""
    for name in package_names:
        assume('\x00' not in name)
        assume('\n' not in name)
        assume('\r' not in name)
    
    captured_output = io.StringIO()
    sys.stdout = captured_output
    try:
        report(*package_names)
    finally:
        sys.stdout = sys.__stdout__
    
    output = captured_output.getvalue()
    lines = output.strip().split('\n')
    assert len(lines) == len(package_names)


@given(st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126)))
def test_output_format_consistency(package_name):
    """Test that output always follows the expected format"""
    assume(len(package_name) > 0)
    assume('\n' not in package_name)
    
    captured_output = io.StringIO()
    sys.stdout = captured_output
    try:
        report(package_name)
    finally:
        sys.stdout = sys.__stdout__
    
    output = captured_output.getvalue().strip()
    # Format should be: package=version{padding} # location
    assert '=' in output
    assert '#' in output
    equals_pos = output.find('=')
    hash_pos = output.find('#')
    assert equals_pos < hash_pos
    
    # Check padding - first part should be 30 chars
    first_part = output[:hash_pos].rstrip()
    assert len(first_part) <= 30


@given(st.text())
def test_command_injection_via_package_name(malicious_input):
    """Test for command injection vulnerability through package names"""
    # Create inputs that might exploit shell=True
    payloads = [
        malicious_input + "; echo INJECTED",
        malicious_input + " && echo INJECTED",
        malicious_input + " | echo INJECTED",
        malicious_input + " `echo INJECTED`",
        malicious_input + " $(echo INJECTED)",
    ]
    
    for payload in payloads:
        assume('\x00' not in payload)
        assume('\n' not in payload)
        assume('\r' not in payload)
        
        captured_output = io.StringIO()
        sys.stdout = captured_output
        try:
            report(payload)
        finally:
            sys.stdout = sys.__stdout__
        
        output = captured_output.getvalue()
        # If INJECTED appears in output, we have command injection
        assert "INJECTED" not in output


@given(st.text(alphabet="0123456789. \t", min_size=1))
def test_version_extraction_logic(version_string):
    """Test the version extraction logic with edge cases"""
    # Mock subprocess to return our version string
    with mock.patch('subprocess.check_output') as mock_check:
        # First call is for 'command -v python'
        mock_check.side_effect = [
            b'/usr/bin/python',  # location check
            version_string.encode()  # version check
        ]
        
        captured_output = io.StringIO()
        sys.stdout = captured_output
        try:
            report('python')
        finally:
            sys.stdout = sys.__stdout__
        
        output = captured_output.getvalue()
        # Check that it doesn't crash and produces output
        assert 'python' in output.lower()
        assert '=' in output


@given(st.text(min_size=1, max_size=100))
@settings(max_examples=200)
def test_special_package_system_handling(extra_text):
    """Test the special 'system' package handling"""
    assume('\x00' not in extra_text)
    assume('\n' not in extra_text)
    
    # Test with 'system' alone and with other packages
    packages = ['system'] if len(extra_text) % 2 == 0 else ['system', extra_text]
    
    captured_output = io.StringIO()
    sys.stdout = captured_output
    try:
        report(*packages)
    finally:
        sys.stdout = sys.__stdout__
    
    output = captured_output.getvalue()
    lines = output.strip().split('\n')
    assert len(lines) == len(packages)
    
    # First line should contain system info
    assert 'system=' in lines[0]
    assert 'OS:' in lines[0]


@given(st.text())
def test_accepted_commands_shell_execution(command_name):
    """Test that only accepted commands can trigger shell execution"""
    # The code only accepts 'python' and 'conda' for shell execution
    assume(command_name not in ['python', 'conda'])
    assume('\x00' not in command_name)
    assume('\n' not in command_name)
    assume('\r' not in command_name)
    
    with mock.patch('subprocess.check_output') as mock_check:
        mock_check.side_effect = Exception("Should not be called")
        
        captured_output = io.StringIO()
        sys.stdout = captured_output
        try:
            report(command_name)
        finally:
            sys.stdout = sys.__stdout__
        
        # For non-accepted commands, subprocess should not be called
        # unless it's a valid Python module
        output = captured_output.getvalue()
        assert command_name in output