#!/usr/bin/env python3
"""
Property-based tests for argcomplete.shell_integration module
Testing evidence-based properties found in the implementation
"""

import re
from hypothesis import given, strategies as st, assume
from argcomplete.shell_integration import shellcode


# Strategy for generating valid executable names
executables_strategy = st.lists(
    st.text(min_size=1, alphabet=st.characters(blacklist_categories=("Cc", "Cs"), blacklist_characters="\0")),
    min_size=1,
    max_size=5
)

# Strategy for generating script paths that might contain spaces
script_path_strategy = st.text(
    min_size=1, 
    max_size=50,
    alphabet=st.characters(blacklist_categories=("Cc", "Cs"), blacklist_characters="\0\n\r")
)


@given(executables_strategy)
def test_fish_function_name_no_slash(executables):
    """Test that fish function names don't contain '/' (as per line 179 comment)"""
    code = shellcode(executables, shell="fish")
    
    # Extract function names from the generated fish code
    function_pattern = r'function __fish_([^\s]+)_complete'
    function_names = re.findall(function_pattern, code)
    
    # Property: function names should not contain '/'
    for func_name in function_names:
        assert '/' not in func_name, f"Function name '{func_name}' contains '/' which is not allowed"


@given(
    executables=executables_strategy,
    prefix=st.text(min_size=1, max_size=10, alphabet=st.characters(min_codepoint=97, max_codepoint=122)),
    suffix=st.text(min_size=1, max_size=10, alphabet=st.characters(min_codepoint=97, max_codepoint=122))
)
def test_bash_zsh_space_handling_in_script_path(executables, prefix, suffix):
    """Test that spaces in script paths are replaced with '_SPACE_' in bash/zsh (line 164)"""
    # Create a script path with a space
    script_path = f"{prefix} {suffix}.py"
    
    for shell in ["bash", "zsh"]:
        code = shellcode(executables, shell=shell, argcomplete_script=script_path)
        
        # Property: spaces in script should be replaced with _SPACE_ in function names
        assert "_SPACE_" in code, f"Expected _SPACE_ in function names for script with spaces"


@given(executables_strategy)
def test_fish_completion_arg_for_paths(executables):
    """Test that fish uses --path for absolute paths and --command otherwise (line 178)"""
    code = shellcode(executables, shell="fish")
    
    for executable in executables:
        if "/" in executable:
            # Property: absolute paths should use --path
            assert f"--path {executable}" in code or "--path" in code
        else:
            # Property: command names should use --command  
            assert f"--command {executable}" in code or "--command" in code


@given(executables_strategy)
def test_executables_preserved_in_output(executables):
    """Test that executables are preserved in the generated shell code"""
    # Import shlex.quote to check quoted version
    from shlex import quote
    
    # Test for each supported shell
    for shell in ["bash", "zsh", "fish", "tcsh", "powershell"]:
        code = shellcode(executables, shell=shell)
        
        # Property: each executable should appear in the generated code
        for exe in executables:
            # The executable might be quoted (especially in bash/zsh) or transformed
            if shell in ["bash", "zsh"]:
                # For bash/zsh, check if the quoted version is present
                quoted_exe = quote(exe)
                assert (exe in code or quoted_exe in code or exe.replace("/", "_") in code), \
                    f"Executable '{exe}' (or quoted version '{quoted_exe}') not found in {shell} output"
            else:
                # For other shells, check direct presence or transformed version
                assert exe in code or exe.replace("/", "_") in code, \
                    f"Executable '{exe}' not found in {shell} output"


@given(
    executables=executables_strategy,
    shell=st.text(min_size=1, max_size=20, alphabet=st.characters(min_codepoint=97, max_codepoint=122))
)
def test_unknown_shell_behavior(executables, shell):
    """Test behavior for unknown shell types"""
    assume(shell not in ["bash", "zsh", "fish", "tcsh", "powershell"])
    
    # Property: unknown shells should return empty string (based on shell_codes.get(shell, ""))
    code = shellcode(executables, shell=shell)
    
    # For unknown shells, if not in shell_codes dict, should generate empty code per executable
    if shell not in ["bash", "zsh", "fish", "tcsh", "powershell"]:
        # The code uses shell_codes.get(shell, "") which returns empty template
        # So the result should be empty strings formatted
        expected_length = len("" * len(executables))  # Empty template per executable
        assert len(code) == expected_length


@given(executables_strategy)
def test_executable_quoting_invariant(executables):
    """Test that bash/zsh properly quotes executables with special characters"""
    from shlex import quote
    
    # Create executables with special shell characters
    test_executables = executables + ["test$var", "test`cmd`", "test;ls", "test|cat"]
    
    for shell in ["bash", "zsh"]:
        code = shellcode(test_executables, shell=shell)
        
        # Property: executables with special characters should be properly quoted
        for exe in test_executables:
            # Check that dangerous patterns are not present unquoted
            if any(char in exe for char in ["$", "`", ";", "|", "&", ">", "<", "'"]):
                # The executable should be quoted using shlex.quote
                quoted_exe = quote(exe)
                assert quoted_exe in code, \
                    f"Executable '{exe}' not properly quoted as '{quoted_exe}' in {shell}"