import sys
import os
import tempfile
import argparse
from unittest import mock
from pathlib import Path

sys.path.insert(0, '/root/hypothesis-llm/envs/sudachipy_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings, example
import sudachipy.command_line as cmd_line


@given(st.text(min_size=256))
@example("A" * 256)  # Exactly 256 bytes - should trigger warning
@example("あ" * 100)  # 300 bytes in UTF-8 (3 bytes per character)
@example("🦄" * 100)  # 400 bytes in UTF-8 (4 bytes per character)
def test_description_truncation_bug(description):
    """
    Bug: The code warns about descriptions > 255 bytes but doesn't actually
    truncate them or prevent them from being passed to build functions.
    This could cause issues in the binary dictionary format.
    """
    desc_bytes = len(description.encode("utf-8"))
    
    if desc_bytes > 255:
        print(f"\nTesting with {desc_bytes} byte description...")
        
        args = argparse.Namespace(
            matrix_file="dummy.matrix",
            in_files=["dummy.csv"],
            out_file="test_output.dic",
            description=description,
            handler=cmd_line._command_build,
            print_usage=lambda: None
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            matrix_file = Path(tmpdir) / "dummy.matrix"
            matrix_file.write_text("dummy matrix content")
            in_file = Path(tmpdir) / "dummy.csv"
            in_file.write_text("dummy,csv,content")
            out_file = Path(tmpdir) / "test_output.dic"
            
            args.matrix_file = str(matrix_file)
            args.in_files = [str(in_file)]
            args.out_file = str(out_file)
            
            # Capture output
            with mock.patch('builtins.print') as mock_print:
                with mock.patch('sudachipy.sudachipy.build_system_dic') as mock_build:
                    # Mock the build function to see what gets passed
                    mock_build.return_value = []
                    
                    # Call the function
                    result = cmd_line._command_build(args, args.print_usage)
                    
                    # Check what happened
                    if mock_build.called:
                        # Bug: The description is passed without truncation!
                        call_args = mock_build.call_args
                        passed_description = call_args.kwargs.get('description', '')
                        
                        print(f"Description passed to build: {len(passed_description.encode('utf-8'))} bytes")
                        print(f"Original description: {desc_bytes} bytes")
                        
                        # This is a bug - descriptions > 255 bytes are passed through
                        assert len(passed_description.encode('utf-8')) == desc_bytes
                        return True  # Bug found
                    else:
                        # Function returns early with just a print
                        print_calls = mock_print.call_args_list
                        if print_calls:
                            # Check if warning was printed
                            for call in print_calls:
                                if 'truncated' in str(call).lower():
                                    print("Warning printed, function returned early")
                                    return False  # No bug, proper early return
        
        return False


if __name__ == "__main__":
    # Run a simple test
    test_description_truncation_bug("A" * 256)