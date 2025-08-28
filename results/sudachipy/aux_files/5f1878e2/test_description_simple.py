import sys
import os
import tempfile
import argparse
from unittest import mock
from pathlib import Path
from io import StringIO

sys.path.insert(0, '/root/hypothesis-llm/envs/sudachipy_env/lib/python3.13/site-packages')
import sudachipy.command_line as cmd_line

def test_description_over_255_bytes():
    """
    Test what happens when description is over 255 bytes.
    The code prints a warning but returns without actually preventing the issue.
    """
    # Create a description that's 256 bytes in UTF-8
    description = "A" * 256
    print(f"Description length: {len(description.encode('utf-8'))} bytes")
    
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
        
        # Capture print output
        captured_output = StringIO()
        with mock.patch('sys.stdout', captured_output):
            with mock.patch('sudachipy.sudachipy.build_system_dic') as mock_build:
                mock_build.return_value = []
                
                # Call the function
                result = cmd_line._command_build(args, args.print_usage)
                
                # Get the output
                output = captured_output.getvalue()
                print(f"Function output: {output}")
                print(f"Function returned: {result}")
                print(f"build_system_dic called: {mock_build.called}")
                
                if mock_build.called:
                    call_args = mock_build.call_args
                    passed_desc = call_args.kwargs.get('description', '')
                    print(f"Description passed to build: '{passed_desc[:50]}...' ({len(passed_desc.encode('utf-8'))} bytes)")

def test_description_at_boundary():
    """Test descriptions at the 255 byte boundary."""
    # Test with exactly 255 bytes
    desc_255 = "A" * 255
    print(f"\n--- Testing with 255 bytes ---")
    print(f"Description: {len(desc_255.encode('utf-8'))} bytes")
    
    args = argparse.Namespace(
        matrix_file="dummy.matrix",
        in_files=["dummy.csv"],
        out_file="test_255.dic",
        description=desc_255,
        handler=cmd_line._command_build,
        print_usage=lambda: None
    )
    
    with tempfile.TemporaryDirectory() as tmpdir:
        matrix_file = Path(tmpdir) / "dummy.matrix"
        matrix_file.write_text("dummy")
        in_file = Path(tmpdir) / "dummy.csv"
        in_file.write_text("dummy")
        out_file = Path(tmpdir) / "test_255.dic"
        
        args.matrix_file = str(matrix_file)
        args.in_files = [str(in_file)]
        args.out_file = str(out_file)
        
        with mock.patch('sudachipy.sudachipy.build_system_dic') as mock_build:
            mock_build.return_value = []
            result = cmd_line._command_build(args, args.print_usage)
            
            if mock_build.called:
                print("build_system_dic was called with 255 byte description")
            else:
                print("build_system_dic was NOT called")

if __name__ == "__main__":
    test_description_over_255_bytes()
    test_description_at_boundary()