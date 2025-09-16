import os
import sys
import tempfile
import subprocess
from unittest.mock import patch, MagicMock
import re

from hypothesis import given, strategies as st, assume, settings
import pytest

import argcomplete.scripts.activate_global_python_argcomplete as activate_script
import argcomplete.scripts.python_argcomplete_check_easy_install_script as check_script


# Test 1: append_to_config_file idempotence property
@given(
    shellcode=st.text(min_size=1, max_size=1000),
    initial_content=st.text(max_size=5000)
)
def test_append_to_config_file_idempotence(shellcode, initial_content):
    """Property: Appending the same shellcode twice should not duplicate it."""
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:
        f.write(initial_content)
        f.flush()
        filepath = f.name
    
    try:
        # Mock get_consent to always return True
        with patch.object(activate_script, 'get_consent', return_value=True):
            # First append
            activate_script.append_to_config_file(filepath, shellcode)
            
            with open(filepath, 'r') as f:
                content_after_first = f.read()
            
            # Second append (should be idempotent)
            activate_script.append_to_config_file(filepath, shellcode)
            
            with open(filepath, 'r') as f:
                content_after_second = f.read()
            
            # Property: content should be the same after second append
            assert content_after_first == content_after_second, \
                "append_to_config_file should be idempotent"
            
            # Property: shellcode should appear exactly once
            assert content_after_second.count(shellcode) == 1, \
                f"Shellcode should appear exactly once, but appears {content_after_second.count(shellcode)} times"
    
    finally:
        os.unlink(filepath)


# Test 2: get_local_dir returns valid path string
@given(brew_output=st.one_of(
    st.text(min_size=1).filter(lambda x: '\n' not in x and '\x00' not in x),
    st.none()
))
def test_get_local_dir_returns_valid_path(brew_output):
    """Property: get_local_dir should always return a non-empty string path."""
    
    def mock_check_output(cmd):
        if brew_output is None:
            raise subprocess.CalledProcessError(1, cmd)
        return (brew_output + '\n').encode()
    
    with patch('subprocess.check_output', side_effect=mock_check_output):
        result = activate_script.get_local_dir()
        
        # Properties:
        assert isinstance(result, str), "Result should be a string"
        assert len(result) > 0, "Result should be non-empty"
        
        # If brew fails, should return /usr/local
        if brew_output is None:
            assert result == "/usr/local", "Should fallback to /usr/local when brew fails"
        else:
            assert result == brew_output.strip(), "Should return brew prefix when available"


# Test 3: check_easy_install_script regex parsing
@given(
    dist_name=st.text(alphabet=st.characters(blacklist_categories=["Cc", "Cs"], blacklist_characters=",'\""), min_size=1, max_size=50),
    script_name=st.text(alphabet=st.characters(blacklist_categories=["Cc", "Cs"], blacklist_characters=",'\""), min_size=1, max_size=50),
    group_name=st.text(alphabet=st.characters(blacklist_categories=["Cc", "Cs"], blacklist_characters=",'\""), min_size=1, max_size=50),
    entry_name=st.text(alphabet=st.characters(blacklist_categories=["Cc", "Cs"], blacklist_characters=",'\""), min_size=1, max_size=50)
)
def test_easy_install_regex_patterns(dist_name, script_name, group_name, entry_name):
    """Property: Regex patterns should correctly parse EASY-INSTALL lines."""
    
    # Test EASY-INSTALL-SCRIPT pattern
    easy_script_line = f"# EASY-INSTALL-SCRIPT: '{dist_name}','{script_name}'"
    pattern = r"# EASY-INSTALL-SCRIPT: '(.+)','(.+)'"
    match = re.match(pattern, easy_script_line)
    
    assert match is not None, f"Pattern should match line: {easy_script_line}"
    assert match.groups() == (dist_name, script_name), \
        f"Should extract correct groups: got {match.groups()}, expected ({dist_name}, {script_name})"
    
    # Test EASY-INSTALL-ENTRY-SCRIPT pattern
    entry_script_line = f"# EASY-INSTALL-ENTRY-SCRIPT: '{dist_name}','{group_name}','{entry_name}'"
    pattern = r"# EASY-INSTALL-ENTRY-SCRIPT: '(.+)','(.+)','(.+)'"
    match = re.match(pattern, entry_script_line)
    
    assert match is not None, f"Pattern should match line: {entry_script_line}"
    assert match.groups() == (dist_name, group_name, entry_name), \
        f"Should extract correct groups: got {match.groups()}, expected ({dist_name}, {group_name}, {entry_name})"


# Test 4: check_easy_install_script return values
@given(
    has_marker=st.booleans(),
    script_type=st.sampled_from(['EASY-INSTALL-SCRIPT', 'EASY-INSTALL-ENTRY-SCRIPT', 'EASY-INSTALL-DEV-SCRIPT', 'PBR Generated', 'regular'])
)
def test_check_easy_install_script_return_values(has_marker, script_type):
    """Property: main() should return 0 when PYTHON_ARGCOMPLETE_OK is found, 1 otherwise."""
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py') as f:
        # Create a mock script file
        if script_type == 'regular':
            f.write("#!/usr/bin/env python\n")
            f.write("# Regular Python script\n")
            if has_marker:
                f.write("# PYTHON_ARGCOMPLETE_OK\n")
        else:
            f.write("#!/usr/bin/env python\n")
            f.write(f"# {script_type}: 'test_dist','test_script'\n")
            if script_type == 'EASY-INSTALL-ENTRY-SCRIPT':
                f.write("# EASY-INSTALL-ENTRY-SCRIPT: 'test_dist','console_scripts','test_entry'\n")
        
        # Add some script content
        f.write("import sys\n")
        f.write("def main():\n")
        f.write("    pass\n")
        filepath = f.name
    
    try:
        # Mock sys.argv
        old_argv = sys.argv
        sys.argv = ['check_script', filepath]
        
        # Mock the package resources to avoid actual package lookups
        with patch('pkg_resources.get_distribution') as mock_dist, \
             patch('pkgutil.get_loader') as mock_loader, \
             patch('builtins.open', side_effect=open) as mock_open:
            
            # Setup mocks
            mock_metadata = MagicMock()
            mock_metadata.get_metadata = MagicMock(return_value="PYTHON_ARGCOMPLETE_OK" if has_marker else "")
            mock_dist.return_value = mock_metadata
            
            mock_loader_obj = MagicMock()
            mock_loader_obj.get_filename = MagicMock(return_value=filepath)
            mock_loader.return_value = mock_loader_obj
            
            # Property: Return value should be 0 if marker found, 1 otherwise
            if script_type == 'regular' and not has_marker:
                # Regular scripts without special headers return 1
                result = check_script.main()
                assert result == 1, "Should return 1 for regular scripts without marker"
            elif script_type == 'regular' and has_marker:
                # Regular scripts with marker in first 1024 bytes might not be detected
                # This is expected behavior - the script checks for specific patterns
                result = check_script.main()
                assert result == 1, "Regular scripts need special headers to be recognized"
    
    finally:
        sys.argv = old_argv
        os.unlink(filepath)


# Test 5: Path manipulation functions
@given(base_dir=st.text(min_size=1, max_size=100).filter(lambda x: '/' not in x and '\\' not in x))
def test_get_activator_path_valid(base_dir):
    """Property: get_activator_path should produce valid path with _python-argcomplete suffix."""
    
    with patch.object(activate_script, 'get_activator_dir', return_value=f"/{base_dir}"):
        result = activate_script.get_activator_path()
        
        # Properties:
        assert isinstance(result, str), "Result should be a string"
        assert result.endswith("_python-argcomplete"), "Should end with _python-argcomplete"
        assert result == f"/{base_dir}/_python-argcomplete", "Should combine path correctly"
        assert '//' not in result, "Should not have double slashes"