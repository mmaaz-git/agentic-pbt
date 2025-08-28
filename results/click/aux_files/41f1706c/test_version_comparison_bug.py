from hypothesis import given, strategies as st, settings
from unittest.mock import patch, MagicMock
import click.shell_completion as shell_completion
import re


def test_version_comparison_bug():
    """Test the string comparison bug in version checking"""
    
    # Test cases showing the bug: string comparison instead of numeric
    test_cases = [
        # (version, should_warn_expected, should_warn_actual, is_bug)
        ("10.0.0", False, True, True),   # Bug: "10" < "4" as strings!
        ("20.0.0", False, True, True),   # Bug: "20" < "4" as strings!
        ("9.5.0", False, False, False),  # OK: "9" > "4" as strings
        ("4.10.0", False, True, True),   # Bug: "10" < "4" as strings!
        ("4.9.0", False, False, False),  # OK: "9" > "4" as strings  
        ("4.3.0", True, True, False),    # OK: Should warn
        ("4.4.0", False, False, False),  # OK: Exact minimum
        ("5.0.0", False, False, False),  # OK: Higher major
        ("3.0.0", True, True, False),    # OK: Should warn
    ]
    
    for version, should_warn_expected, should_warn_actual, is_bug in test_cases:
        mock_result = MagicMock()
        mock_result.stdout = version.encode()
        
        with patch('subprocess.run', return_value=mock_result):
            with patch('shutil.which', return_value='/bin/bash'):
                with patch('click.shell_completion.echo') as mock_echo:
                    shell_completion.BashComplete._check_version()
                    
                    warned = mock_echo.called
                    
                    status = "BUG!" if is_bug else "OK"
                    print(f"Version {version:10} -> {'WARN' if warned else 'PASS':4} (expected {'WARN' if should_warn_expected else 'PASS':4}) {status}")
                    
                    # Verify it matches our expectation
                    assert warned == should_warn_actual, f"Version {version} behaved unexpectedly"


def demonstrate_string_comparison_issue():
    """Demonstrate the core issue with string comparison"""
    print("\nDemonstrating string vs numeric comparison:")
    print(f'"10" < "4" = {"10" < "4"}  (string comparison - WRONG!)')
    print(f'10 < 4 = {10 < 4}  (numeric comparison - correct)')
    print(f'"4" == "4" and "10" < "4" = {"4" == "4" and "10" < "4"}  (the actual bug condition)')
    
    print("\nThis means Bash version 4.10+ would incorrectly trigger the warning!")


def test_reproducer():
    """Direct reproducer for the bug"""
    # Simulate Bash 4.10 (a valid version that should NOT warn)
    version_output = "4.10.0(1)-release"
    
    mock_result = MagicMock()
    mock_result.stdout = version_output.encode()
    
    with patch('subprocess.run', return_value=mock_result):
        with patch('shutil.which', return_value='/bin/bash'):
            with patch('click.shell_completion.echo') as mock_echo:
                shell_completion.BashComplete._check_version()
                
                if mock_echo.called:
                    print(f"\nBUG CONFIRMED: Bash {version_output} incorrectly triggers warning!")
                    print("Warning message:", mock_echo.call_args[0][0])
                    return True
    
    return False


if __name__ == "__main__":
    print("Testing version comparison bug...")
    test_version_comparison_bug()
    demonstrate_string_comparison_issue()
    
    if test_reproducer():
        print("\n✓ Successfully reproduced the bug!")