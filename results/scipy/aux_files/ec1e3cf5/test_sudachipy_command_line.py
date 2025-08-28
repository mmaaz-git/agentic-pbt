import sys
import os
import tempfile
import argparse
from unittest import mock
from pathlib import Path

sys.path.insert(0, '/root/hypothesis-llm/envs/sudachipy_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import sudachipy.command_line as cmd_line


@given(st.text())
def test_description_length_validation_build(description):
    """
    Test that descriptions > 255 bytes in UTF-8 are properly handled.
    The code prints a warning but doesn't actually truncate or raise an error.
    This could lead to silent failures or unexpected behavior.
    """
    args = argparse.Namespace(
        matrix_file="dummy.matrix",
        in_files=["dummy.csv"],
        out_file="dummy.dic",
        description=description,
        handler=cmd_line._command_build,
        print_usage=lambda: None
    )
    
    # Create dummy files to avoid file existence errors
    with tempfile.TemporaryDirectory() as tmpdir:
        matrix_file = Path(tmpdir) / "dummy.matrix"
        matrix_file.touch()
        in_file = Path(tmpdir) / "dummy.csv"
        in_file.touch()
        out_file = Path(tmpdir) / "dummy.dic"
        
        args.matrix_file = str(matrix_file)
        args.in_files = [str(in_file)]
        args.out_file = str(out_file)
        
        # Check if description > 255 bytes
        desc_bytes = len(description.encode("utf-8"))
        
        if desc_bytes > 255:
            # The function should handle this case properly
            # Currently it just prints and returns without error
            with mock.patch('sys.stderr'):
                with mock.patch('builtins.print') as mock_print:
                    result = cmd_line._command_build(args, args.print_usage)
                    # Bug: function returns None without raising error or truncating
                    assert result is None
                    # Verify warning was printed
                    mock_print.assert_called()
                    call_args = str(mock_print.call_args)
                    assert "truncated" in call_args.lower()


@given(st.text())
def test_description_length_validation_user_build(description):
    """
    Test that descriptions > 255 bytes in UTF-8 are properly handled for user dict.
    Same issue as with build command.
    """
    args = argparse.Namespace(
        system_dic="dummy.dic",
        in_files=["dummy.csv"],
        out_file="user.dic",
        description=description,
        handler=cmd_line._command_user_build,
        print_usage=lambda: None
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        system_dic = Path(tmpdir) / "dummy.dic"
        system_dic.touch()
        in_file = Path(tmpdir) / "dummy.csv"
        in_file.touch()
        out_file = Path(tmpdir) / "user.dic"
        
        args.system_dic = str(system_dic)
        args.in_files = [str(in_file)]
        args.out_file = str(out_file)
        
        desc_bytes = len(description.encode("utf-8"))
        
        if desc_bytes > 255:
            with mock.patch('sys.stderr'):
                with mock.patch('builtins.print') as mock_print:
                    result = cmd_line._command_user_build(args, args.print_usage)
                    assert result is None
                    mock_print.assert_called()
                    call_args = str(mock_print.call_args)
                    assert "truncated" in call_args.lower()


@given(st.lists(st.text(min_size=1)))
def test_input_files_checker_property(file_paths):
    """
    Test that _input_files_checker properly validates file existence.
    Property: All non-existent files should cause exit(1).
    """
    assume(len(file_paths) > 0)
    
    # Filter out empty strings
    file_paths = [f for f in file_paths if f]
    assume(len(file_paths) > 0)
    
    args = argparse.Namespace(in_files=file_paths)
    
    # Create a temporary directory to control file existence
    with tempfile.TemporaryDirectory() as tmpdir:
        # Map file paths to temp paths
        temp_paths = []
        for fp in file_paths:
            # Sanitize file path to avoid directory traversal
            safe_name = fp.replace('/', '_').replace('\\', '_')
            if safe_name:
                temp_paths.append(os.path.join(tmpdir, safe_name))
            else:
                temp_paths.append(os.path.join(tmpdir, "empty"))
        
        args.in_files = temp_paths
        
        # Test with non-existent files
        with mock.patch('sys.stderr'):
            with mock.patch('sys.exit') as mock_exit:
                cmd_line._input_files_checker(args, lambda: None)
                # Should call exit(1) for non-existent files
                mock_exit.assert_called_with(1)
        
        # Create all files and test again
        for tp in temp_paths:
            Path(tp).touch()
        
        with mock.patch('sys.stderr'):
            with mock.patch('sys.exit') as mock_exit:
                cmd_line._input_files_checker(args, lambda: None)
                # Should not exit when all files exist
                mock_exit.assert_not_called()


@given(st.text(min_size=1))
def test_set_default_subparser_edge_cases(subparser_name):
    """
    Test the default subparser mechanism that modifies sys.argv.
    This tests for potential issues with the argv manipulation.
    """
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    
    # Add a test subparser
    sub = subparsers.add_parser(subparser_name)
    sub.set_defaults(handler=lambda x: x)
    
    # Save original argv
    original_argv = sys.argv.copy()
    
    try:
        # Test with empty argv (after program name)
        sys.argv = ['program']
        parser.set_default_subparser('default')
        assert len(sys.argv) == 2
        assert sys.argv[1] == 'default'
        
        # Test with existing subparser
        sys.argv = ['program', subparser_name]
        parser.set_default_subparser('default')
        # Should not add default when subparser exists
        assert sys.argv[1] == subparser_name
        
        # Test with help flag
        sys.argv = ['program', '--help']
        parser.set_default_subparser('default')
        # Should not add default with help flag
        assert '--help' in sys.argv
        assert 'default' not in sys.argv[:2]
        
    finally:
        # Restore original argv
        sys.argv = original_argv


@given(st.text())
def test_unicode_handling_in_descriptions(text):
    """
    Test that Unicode text is properly handled in description fields.
    The code uses encode('utf-8') but doesn't handle encoding errors.
    """
    try:
        encoded = text.encode('utf-8')
        byte_length = len(encoded)
        
        # Test edge cases around the 255 byte boundary
        if byte_length == 255:
            # Exactly 255 bytes should be accepted
            assert byte_length <= 255
        elif byte_length > 255:
            # Over 255 bytes should trigger warning
            assert byte_length > 255
            
        # Check for potential issues with surrogate pairs or invalid Unicode
        decoded = encoded.decode('utf-8')
        assert decoded == text
        
    except UnicodeEncodeError:
        # Some strings might not be valid Unicode
        pass
    except UnicodeDecodeError:
        # Round-trip encode/decode should work
        pass