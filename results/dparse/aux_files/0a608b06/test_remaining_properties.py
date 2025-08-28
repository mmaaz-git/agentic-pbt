"""Test remaining properties that didn't have bugs"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/dparse_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings
import dparse.filetypes as filetypes
from dparse.dependencies import DependencyFile

# Test valid file types always result in a parser being assigned
@given(st.sampled_from([
    filetypes.requirements_txt,
    filetypes.conda_yml,
    filetypes.setup_cfg,
    filetypes.tox_ini,
    filetypes.pipfile,
    filetypes.pipfile_lock,
    filetypes.poetry_lock,
    filetypes.pyproject_toml
]))
@settings(max_examples=100)
def test_valid_file_type_always_has_parser(file_type):
    """Test that valid file types always result in a parser being assigned"""
    content = ""
    df = DependencyFile(content=content, file_type=file_type)
    assert hasattr(df, 'parser')
    assert df.parser is not None

# Test path endings uniquely determine parser
@given(st.sampled_from([
    "requirements.txt", "test.txt", "requirements.in",
    "environment.yml", "conda.yml",
    "setup.cfg",
    "tox.ini", "test.ini",
    "Pipfile",
    "Pipfile.lock",
    "poetry.lock",
    "pyproject.toml"
]))
@settings(max_examples=100)
def test_path_ending_determines_parser(path):
    """Test that file path endings uniquely determine the parser"""
    content = ""
    df = DependencyFile(content=content, path=path)
    assert hasattr(df, 'parser')
    assert df.parser is not None
    
    # Parser class should be consistent for the same path
    df2 = DependencyFile(content=content, path=path)
    assert df.parser.__class__ == df2.parser.__class__


if __name__ == "__main__":
    print("Testing remaining properties...")
    
    test_valid_file_type_always_has_parser()
    print("✓ Valid file types always have parsers")
    
    test_path_ending_determines_parser()
    print("✓ Path endings uniquely determine parser")
    
    print("\nAll remaining tests passed!")