"""Reproduce the JSON Lines bug in json.tool"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def test_json_lines_simple():
    """Minimal reproduction of the JSON Lines bug"""
    
    # Create a simple JSON Lines file with one object
    data = [{"key": "value"}]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        for item in data:
            json.dump(item, f)
            f.write('\n')
        input_file = f.name
    
    print(f"Created test file: {input_file}")
    print(f"File contents: {Path(input_file).read_text()}")
    
    try:
        # Try to process with json.tool using --json-lines
        result = subprocess.run(
            [sys.executable, '-m', 'json.tool', '--json-lines', '--no-indent', input_file],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        print(f"Return code: {result.returncode}")
        print(f"Stdout: {result.stdout}")
        print(f"Stderr: {result.stderr}")
        
        if result.returncode != 0:
            print(f"ERROR: json.tool failed with --json-lines")
            print(f"Error message: {result.stderr}")
            return False
        
        return True
    finally:
        Path(input_file).unlink()


def test_direct_json_lines():
    """Test json.tool directly with stdin"""
    data = [{"a": 1}, {"b": 2}]
    input_text = '\n'.join(json.dumps(item) for item in data)
    
    print("Testing with stdin input:")
    print(f"Input: {input_text}")
    
    result = subprocess.run(
        [sys.executable, '-m', 'json.tool', '--json-lines', '--no-indent'],
        input=input_text,
        capture_output=True,
        text=True
    )
    
    print(f"Return code: {result.returncode}")
    print(f"Stdout: {result.stdout}")
    print(f"Stderr: {result.stderr}")
    
    return result.returncode == 0


if __name__ == "__main__":
    print("=" * 60)
    print("Test 1: JSON Lines with file input")
    print("=" * 60)
    success1 = test_json_lines_simple()
    
    print("\n" + "=" * 60)
    print("Test 2: JSON Lines with stdin")
    print("=" * 60)
    success2 = test_direct_json_lines()
    
    print("\n" + "=" * 60)
    if success1 and success2:
        print("✓ All tests passed")
    else:
        print("✗ Bug confirmed in json.tool --json-lines")