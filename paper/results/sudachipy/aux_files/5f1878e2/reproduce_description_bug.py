#!/usr/bin/env python3
"""
Reproduces the description truncation bug in sudachipy.command_line.

The bug: When a description is > 255 bytes in UTF-8, the code prints
"it will be truncated" but actually just returns without building the dictionary.
This is misleading and causes silent failures.
"""

import sys
import os
import tempfile
import argparse
from pathlib import Path
from unittest import mock

sys.path.insert(0, '/root/hypothesis-llm/envs/sudachipy_env/lib/python3.13/site-packages')
import sudachipy.command_line as cmd_line


def reproduce_bug():
    print("=== Reproducing Description Truncation Bug ===\n")
    
    # Create a description that's 256 bytes (just over the limit)
    description = "A" * 256
    print(f"Testing with description of {len(description.encode('utf-8'))} bytes")
    print(f"Description: '{description[:50]}...' (truncated for display)\n")
    
    # Set up arguments as if running: sudachipy build -m matrix.def -o out.dic in.csv -d "AAA..."
    args = argparse.Namespace(
        matrix_file="matrix.def",
        in_files=["input.csv"],
        out_file="output.dic",
        description=description,
        handler=cmd_line._command_build,
        print_usage=lambda: print("[print_usage would be called here]")
    )
    
    # Create temporary files to simulate real usage
    with tempfile.TemporaryDirectory() as tmpdir:
        matrix_file = Path(tmpdir) / "matrix.def"
        matrix_file.write_text("0 0 0")  # Minimal matrix content
        
        in_file = Path(tmpdir) / "input.csv"
        in_file.write_text("test,0,0,0,テスト,*,*,*,*,*,*,*,*")  # Minimal CSV
        
        args.matrix_file = str(matrix_file)
        args.in_files = [str(in_file)]
        args.out_file = str(Path(tmpdir) / "output.dic")
        
        print("Expected behavior: Either truncate the description or raise an error")
        print("Actual behavior: Prints misleading message and returns without building\n")
        
        # Mock the actual build function to track if it's called
        with mock.patch('sudachipy.sudachipy.build_system_dic') as mock_build:
            mock_build.return_value = [("test", 100, 0.1)]
            
            # Capture print output
            with mock.patch('builtins.print') as mock_print:
                # Call the command
                result = cmd_line._command_build(args, args.print_usage)
                
                # Check what was printed
                print_calls = [str(call) for call in mock_print.call_args_list]
                for call in print_calls:
                    if 'truncated' in call.lower():
                        print(f"Message printed: {call}")
                
                print(f"\nFunction returned: {result}")
                print(f"build_system_dic called: {mock_build.called}")
                
                if not mock_build.called:
                    print("\n🐛 BUG CONFIRMED: The function returns early without building the dictionary!")
                    print("   The message says 'it will be truncated' but nothing is actually truncated.")
                    print("   The dictionary is never built, causing a silent failure.")
                    return True
    
    return False


def test_boundary_cases():
    """Test edge cases around the 255 byte boundary."""
    print("\n=== Testing Boundary Cases ===\n")
    
    test_cases = [
        ("A" * 254, "254 bytes - should work"),
        ("A" * 255, "255 bytes - should work"),
        ("A" * 256, "256 bytes - triggers bug"),
        ("あ" * 85,  "255 bytes UTF-8 (Japanese) - should work"),
        ("あ" * 86,  "258 bytes UTF-8 (Japanese) - triggers bug"),
    ]
    
    for desc, label in test_cases:
        byte_len = len(desc.encode('utf-8'))
        print(f"{label}: {byte_len} bytes")
        
        args = argparse.Namespace(
            matrix_file="dummy",
            in_files=["dummy"],
            out_file="dummy",
            description=desc,
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create dummy files
            Path(tmpdir, "dummy").touch()
            args.matrix_file = str(Path(tmpdir, "dummy"))
            args.in_files = [str(Path(tmpdir, "dummy"))]
            args.out_file = str(Path(tmpdir, "out"))
            
            with mock.patch('sudachipy.sudachipy.build_system_dic') as mock_build:
                mock_build.return_value = []
                with mock.patch('builtins.print'):
                    result = cmd_line._command_build(args, lambda: None)
                    
                    if byte_len > 255:
                        if not mock_build.called:
                            print(f"  ❌ Bug: Function returned without building (returned {result})")
                        else:
                            print(f"  ✓ Dictionary built successfully")
                    else:
                        if mock_build.called:
                            print(f"  ✓ Dictionary built successfully")
                        else:
                            print(f"  ❌ Unexpected: Dictionary not built for valid description")


if __name__ == "__main__":
    bug_found = reproduce_bug()
    test_boundary_cases()
    
    if bug_found:
        print("\n" + "="*50)
        print("BUG SUMMARY:")
        print("The _command_build and _command_user_build functions have a bug where")
        print("descriptions > 255 bytes cause the function to return early with just")
        print("a misleading print statement, without actually truncating or building")
        print("the dictionary. This causes silent failures in dictionary building.")
        print("="*50)