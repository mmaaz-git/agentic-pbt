from hypothesis import given, strategies as st, settings
from unittest.mock import patch, MagicMock
import click.shell_completion as shell_completion
import subprocess
import io
import sys


@given(st.text())
@settings(max_examples=200)
def test_bash_version_parsing_never_crashes(version_output):
    """BashComplete._check_version should handle any bash version output"""
    
    # Mock subprocess.run to return our generated output
    mock_result = MagicMock()
    mock_result.stdout = version_output.encode()
    
    # Capture stderr to check error messages
    captured_err = io.StringIO()
    
    with patch('subprocess.run', return_value=mock_result):
        with patch('shutil.which', return_value='/bin/bash'):
            with patch('click.shell_completion.echo') as mock_echo:
                # This should never crash
                shell_completion.BashComplete._check_version()
                
                # Check if error messages were printed correctly
                if mock_echo.called:
                    # Should only print to stderr with err=True
                    for call in mock_echo.call_args_list:
                        if len(call[1]) > 0 and 'err' in call[1]:
                            assert call[1]['err'] == True


def test_bash_version_edge_cases():
    """Test specific edge cases for bash version checking"""
    
    test_cases = [
        # (version_string, should_warn)
        ("4.4.0", False),  # Valid, recent version
        ("5.0.0", False),  # Valid, recent version
        ("3.2.57(1)-release", True),  # Old version
        ("4.3.48(1)-release", True),  # Just below 4.4
        ("", True),  # Empty output
        ("invalid", True),  # Invalid format
        ("bash-4.4", True),  # Different format
        ("GNU bash, version 4.4.0(1)-release", False),  # Full format
        ("1.0.0", True),  # Very old
        ("10.0.0", False),  # Future version
    ]
    
    for version_output, should_warn in test_cases:
        mock_result = MagicMock()
        mock_result.stdout = version_output.encode()
        
        with patch('subprocess.run', return_value=mock_result):
            with patch('shutil.which', return_value='/bin/bash'):
                with patch('click.shell_completion.echo') as mock_echo:
                    shell_completion.BashComplete._check_version()
                    
                    if should_warn:
                        assert mock_echo.called, f"Expected warning for version: {version_output}"
                    else:
                        assert not mock_echo.called, f"Unexpected warning for version: {version_output}"
        
        print(f"Version {version_output!r:40} -> {'WARN' if should_warn else 'OK'}")


def test_bash_not_found():
    """Test when bash is not found on the system"""
    with patch('shutil.which', return_value=None):
        with patch('click.shell_completion.echo') as mock_echo:
            shell_completion.BashComplete._check_version()
            
            # Should print error message
            assert mock_echo.called
            assert "Couldn't detect Bash version" in str(mock_echo.call_args)


if __name__ == "__main__":
    test_bash_version_edge_cases()
    test_bash_not_found()
    print("\nAll manual tests passed!")