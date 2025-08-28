#!/usr/bin/env python3
"""Minimal reproduction of the non-dict YAML crash bug."""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, '/root/hypothesis-llm/envs/copier_env/lib/python3.13/site-packages')

from copier._subproject import Subproject

# Create a temporary directory
with tempfile.TemporaryDirectory() as tmpdir:
    tmpdir_path = Path(tmpdir)
    answers_file = tmpdir_path / ".copier-answers.yml"
    
    # Write non-dict YAML content (a simple integer)
    with answers_file.open("w") as f:
        f.write("42")
    
    # Create Subproject instance
    subproject = Subproject(local_abspath=tmpdir_path)
    
    # This crashes with AttributeError
    print(subproject.last_answers)