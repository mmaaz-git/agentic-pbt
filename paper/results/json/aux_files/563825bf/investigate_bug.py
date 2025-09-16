"""Deep investigation of the json.tool bug"""

import json
import sys
import tempfile
from pathlib import Path


def simulate_json_tool_logic():
    """Simulate the logic from json.tool to understand the bug"""
    
    # Create a test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        json.dump({"test": "data"}, f)
        f.write('\n')
        json.dump({"more": "data"}, f)
        f.write('\n')
        input_file = f.name
    
    print(f"Test file created: {input_file}")
    print(f"Contents: {Path(input_file).read_text()}")
    
    # Simulate json.tool's logic (from lines 60-71)
    try:
        infile = open(input_file, encoding='utf-8')
        try:
            # This is what json.tool does for --json-lines
            objs = (json.loads(line) for line in infile)
            
            # The issue: infile gets closed here!
        finally:
            if infile is not sys.stdin:
                infile.close()  # <-- File closed here
        
        # But then json.tool tries to iterate over objs (line 78-79)
        # which still references the closed file!
        print("Trying to iterate over generator after file is closed...")
        for obj in objs:
            print(f"Object: {obj}")
            
    except Exception as e:
        print(f"ERROR: {e}")
        print(f"This is the bug! The generator references a closed file.")
    finally:
        Path(input_file).unlink()


def demonstrate_fix():
    """Demonstrate how the bug could be fixed"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        json.dump({"test": "data"}, f)
        f.write('\n')
        json.dump({"more": "data"}, f)
        f.write('\n')
        input_file = f.name
    
    print("\nDemonstrating a fix:")
    print("Convert generator to list before closing file...")
    
    try:
        infile = open(input_file, encoding='utf-8')
        try:
            # Fix: Convert generator to list BEFORE closing the file
            objs = list(json.loads(line) for line in infile)
        finally:
            if infile is not sys.stdin:
                infile.close()
        
        # Now we can iterate safely
        for obj in objs:
            print(f"Object: {obj}")
        print("✓ Success! No error when generator is converted to list")
            
    finally:
        Path(input_file).unlink()


if __name__ == "__main__":
    print("=" * 60)
    print("Reproducing the bug in json.tool logic:")
    print("=" * 60)
    simulate_json_tool_logic()
    
    print("\n" + "=" * 60)
    print("Demonstrating the fix:")
    print("=" * 60)
    demonstrate_fix()