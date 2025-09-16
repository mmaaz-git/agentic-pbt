"""Direct tests to demonstrate bugs in copier.cli."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, '/root/hypothesis-llm/envs/copier_env/lib/python3.13/site-packages')

from copier._cli import _Subcommand


def test_data_switch_without_equals():
    """Demonstrate that data_switch crashes when given a value without '='."""
    subcommand = _Subcommand(executable="test")
    
    # This should crash with ValueError: not enough values to unpack
    try:
        subcommand.data_switch(["VARIABLE_WITHOUT_EQUALS"])
        print("ERROR: Expected ValueError but none was raised!")
    except ValueError as e:
        print(f"BUG FOUND: data_switch crashes with: {e}")
        print("Input: 'VARIABLE_WITHOUT_EQUALS' (no '=' sign)")
        return True
    return False


def test_data_file_switch_empty_yaml():
    """Demonstrate that data_file_switch crashes on empty YAML files."""
    subcommand = _Subcommand(executable="test")
    
    # Create an empty YAML file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        # Empty file - yaml.safe_load will return None
        temp_path = f.name
    
    try:
        # This should crash with AttributeError: 'NoneType' object has no attribute 'items'
        try:
            subcommand.data_file_switch(temp_path)
            print("ERROR: Expected AttributeError but none was raised!")
        except AttributeError as e:
            print(f"BUG FOUND: data_file_switch crashes with: {e}")
            print(f"Input: Empty YAML file at {temp_path}")
            return True
    finally:
        Path(temp_path).unlink(missing_ok=True)
    
    return False


def test_data_switch_empty_string():
    """Test data_switch with an empty string."""
    subcommand = _Subcommand(executable="test")
    
    try:
        subcommand.data_switch([""])
        print("ERROR: Expected ValueError but none was raised!")
    except ValueError as e:
        print(f"BUG FOUND: data_switch crashes on empty string with: {e}")
        return True
    return False


def test_data_switch_equals_only():
    """Test data_switch with just an equals sign."""
    subcommand = _Subcommand(executable="test")
    
    try:
        # This should work - splits into "" and ""
        subcommand.data_switch(["="])
        print("Interestingly, '=' alone works - creates empty key with empty value")
        print(f"Result: data = {subcommand.data}")
        return False
    except Exception as e:
        print(f"Unexpected error with '=': {e}")
        return True


if __name__ == "__main__":
    print("Testing copier._cli for bugs...")
    print("=" * 60)
    
    bugs_found = []
    
    print("\nTest 1: data_switch without equals sign")
    print("-" * 40)
    if test_data_switch_without_equals():
        bugs_found.append("data_switch crashes on input without '='")
    
    print("\nTest 2: data_file_switch with empty YAML")
    print("-" * 40)
    if test_data_file_switch_empty_yaml():
        bugs_found.append("data_file_switch crashes on empty YAML files")
    
    print("\nTest 3: data_switch with empty string")
    print("-" * 40)
    if test_data_switch_empty_string():
        bugs_found.append("data_switch crashes on empty string")
    
    print("\nTest 4: data_switch with equals only")
    print("-" * 40)
    test_data_switch_equals_only()
    
    print("\n" + "=" * 60)
    print(f"SUMMARY: Found {len(bugs_found)} bug(s)")
    for i, bug in enumerate(bugs_found, 1):
        print(f"  {i}. {bug}")