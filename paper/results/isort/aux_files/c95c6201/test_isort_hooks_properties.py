import sys
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock
from hypothesis import given, strategies as st, assume

# Add isort to path
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

import isort.hooks as hooks


# Test property: get_lines should always strip whitespace from all lines
@given(st.lists(st.text()))
def test_get_lines_strips_whitespace(lines_with_whitespace):
    # Create mock stdout with lines that have leading/trailing whitespace
    mock_lines = []
    for line in lines_with_whitespace:
        # Add random whitespace
        mock_lines.append(f"  {line}  \t\n")
    
    mock_stdout = "".join(mock_lines)
    
    with patch('isort.hooks.get_output') as mock_get_output:
        mock_get_output.return_value = mock_stdout
        result = hooks.get_lines(['fake', 'command'])
        
        # Property: No line should have leading or trailing whitespace
        for line in result:
            assert line == line.strip(), f"Line '{line}' has whitespace"
            # Also verify it matches the expected stripped version
            if result:
                for i, original in enumerate(lines_with_whitespace[:len(result)]):
                    assert result[i] == original.strip()


# Test property: git_hook with strict=False should always return 0
@given(
    st.integers(min_value=0, max_value=100),  # number of errors
    st.booleans(),  # modify flag
    st.booleans(),  # lazy flag
)
def test_git_hook_strict_false_returns_zero(num_errors, modify, lazy):
    with patch('isort.hooks.get_lines') as mock_get_lines:
        # Mock finding some Python files
        if num_errors > 0:
            mock_get_lines.return_value = ['file1.py', 'file2.py']
        else:
            mock_get_lines.return_value = []
        
        with patch('isort.hooks.get_output') as mock_get_output:
            mock_get_output.return_value = "import os\nimport sys"
            
            with patch('isort.api.check_code_string') as mock_check:
                # Simulate errors
                mock_check.return_value = False if num_errors > 0 else True
                
                with patch('isort.api.sort_file'):
                    # Property: strict=False should always return 0
                    result = hooks.git_hook(strict=False, modify=modify, lazy=lazy)
                    assert result == 0, f"strict=False should return 0, got {result}"


# Test property: git_hook with strict=True should return the error count
@given(
    st.lists(st.text(min_size=1).filter(lambda x: x.endswith('.py')), min_size=0, max_size=10),
    st.booleans(),  # modify flag
    st.booleans(),  # lazy flag
)
def test_git_hook_strict_true_returns_error_count(python_files, modify, lazy):
    with patch('isort.hooks.get_lines') as mock_get_lines:
        mock_get_lines.return_value = python_files
        
        with patch('isort.hooks.get_output') as mock_get_output:
            mock_get_output.return_value = "import os\nimport sys"
            
            with patch('isort.api.check_code_string') as mock_check:
                # Each file will generate an error
                mock_check.return_value = False
                
                with patch('isort.api.sort_file'):
                    result = hooks.git_hook(strict=True, modify=modify, lazy=lazy)
                    # Property: strict=True should return the number of errors
                    expected_errors = len(python_files)
                    assert result == expected_errors, f"Expected {expected_errors} errors, got {result}"


# Test property: empty files_modified should always return 0
@given(
    st.booleans(),  # strict
    st.booleans(),  # modify
    st.booleans(),  # lazy
    st.text(),      # settings_file
    st.lists(st.text(), min_size=0, max_size=5),  # directories
)
def test_git_hook_empty_files_returns_zero(strict, modify, lazy, settings_file, directories):
    with patch('isort.hooks.get_lines') as mock_get_lines:
        # Property: when no files are modified, should return 0
        mock_get_lines.return_value = []
        
        result = hooks.git_hook(
            strict=strict, 
            modify=modify, 
            lazy=lazy,
            settings_file=settings_file,
            directories=directories if directories else None
        )
        assert result == 0, f"Empty files should return 0, got {result}"


# Test property: get_output return value is always a string
@given(st.binary())
def test_get_output_returns_decoded_string(binary_output):
    mock_result = MagicMock()
    mock_result.stdout = binary_output
    
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = mock_result
        
        try:
            result = hooks.get_output(['fake', 'command'])
            # Property: result should always be a string
            assert isinstance(result, str), f"Expected string, got {type(result)}"
        except UnicodeDecodeError:
            # This is expected for invalid UTF-8 sequences
            pass


# Test metamorphic property: directories parameter filters files
@given(
    st.lists(st.text(min_size=1), min_size=1, max_size=5),  # directories to filter
    st.lists(st.text(min_size=1), min_size=1, max_size=10),  # all files
)
def test_git_hook_directories_filter(directories, all_files):
    # Ensure some files end with .py
    all_files = [f"{f}.py" if not f.endswith('.py') else f for f in all_files]
    
    with patch('isort.hooks.get_lines') as mock_get_lines:
        # Track what command was called with
        called_commands = []
        def capture_command(cmd):
            called_commands.append(cmd)
            return all_files
        mock_get_lines.side_effect = capture_command
        
        with patch('isort.hooks.get_output') as mock_get_output:
            mock_get_output.return_value = "import os"
            
            with patch('isort.api.check_code_string') as mock_check:
                mock_check.return_value = True
                
                # Call with directories
                hooks.git_hook(directories=directories)
                
                # Property: directories should be appended to git command
                assert len(called_commands) > 0
                last_command = called_commands[-1]
                for dir in directories:
                    assert dir in last_command, f"Directory {dir} not in command"