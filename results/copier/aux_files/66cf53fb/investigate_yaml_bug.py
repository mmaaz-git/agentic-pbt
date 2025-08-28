#!/usr/bin/env python3
"""Investigate the YAML loading behavior."""

import sys
import tempfile
from pathlib import Path
import yaml

sys.path.insert(0, '/root/hypothesis-llm/envs/copier_env/lib/python3.13/site-packages')

from copier._subproject import Subproject, load_answersfile_data

# Test cases that return non-dict values
test_cases = [
    ("0", 0),
    ("1", 1),
    ("true", True),
    ("false", False),
    ("null", None),
    ('"string"', "string"),
    ('["list", "items"]', ["list", "items"]),
    ("42.5", 42.5),
]

print("Testing load_answersfile_data with scalar YAML values:")
print("=" * 60)

for yaml_content, expected in test_cases:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        answers_file = ".copier-answers.yml"
        file_path = tmpdir_path / answers_file
        
        # Write YAML content
        with file_path.open("w") as f:
            f.write(yaml_content)
        
        # Load using load_answersfile_data
        result = load_answersfile_data(tmpdir_path, answers_file)
        
        print(f"YAML: {yaml_content:20} -> Result type: {type(result).__name__:10} Value: {result}")
        
        # Test with Subproject
        try:
            subproject = Subproject(local_abspath=tmpdir_path)
            last_answers = subproject.last_answers
            print(f"  Subproject.last_answers type: {type(last_answers).__name__}, Value: {last_answers}")
        except Exception as e:
            print(f"  Subproject ERROR: {e}")
        print("-" * 60)