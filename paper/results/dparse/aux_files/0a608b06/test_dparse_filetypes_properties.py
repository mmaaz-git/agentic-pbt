"""Property-based tests for dparse.filetypes module"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/dparse_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import dparse.filetypes as filetypes
from dparse import parse
from dparse.dependencies import DependencyFile


# Property 1: File type constants should match expected file names/paths that trigger the same parser
def test_file_type_path_consistency():
    """Test that file type constants match the file paths that trigger the same parser"""
    
    # Map of file type constants to expected file path patterns
    file_type_to_paths = {
        filetypes.requirements_txt: ["requirements.txt", "requirements.in", "test.txt"],
        filetypes.conda_yml: ["environment.yml", "conda.yml"],
        filetypes.setup_cfg: ["setup.cfg"],
        filetypes.tox_ini: ["tox.ini", "test.ini"],
        filetypes.pipfile: ["Pipfile"],
        filetypes.pipfile_lock: ["Pipfile.lock"],
        filetypes.poetry_lock: ["poetry.lock"],
        filetypes.pyproject_toml: ["pyproject.toml"]
    }
    
    # Empty content is sufficient for parser selection
    content = ""
    
    for file_type, paths in file_type_to_paths.items():
        # Create with explicit file_type
        df_with_type = DependencyFile(content=content, file_type=file_type)
        parser_class_with_type = df_with_type.parser.__class__
        
        for path in paths:
            # Create with path inference
            df_with_path = DependencyFile(content=content, path=path)
            parser_class_with_path = df_with_path.parser.__class__
            
            # They should use the same parser class
            assert parser_class_with_type == parser_class_with_path, \
                f"File type {file_type} and path {path} should use same parser, " \
                f"but got {parser_class_with_type.__name__} vs {parser_class_with_path.__name__}"


# Property 2: Serialization round-trip should preserve file_type
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
def test_serialization_round_trip(file_type):
    """Test that file_type is preserved through serialize/deserialize cycle"""
    
    # Create a DependencyFile with the given file_type
    content = ""
    original = DependencyFile(content=content, file_type=file_type, path="test.file")
    
    # Serialize and deserialize
    serialized = original.serialize()
    deserialized = DependencyFile.deserialize(serialized)
    
    # File type should be preserved
    assert deserialized.file_type == original.file_type, \
        f"File type not preserved: {original.file_type} != {deserialized.file_type}"


# Property 3: All file type constants should be valid strings
def test_file_type_constants_are_strings():
    """Test that all file type constants are non-empty strings"""
    
    file_types = [
        filetypes.requirements_txt,
        filetypes.conda_yml,
        filetypes.setup_cfg,
        filetypes.tox_ini,
        filetypes.pipfile,
        filetypes.pipfile_lock,
        filetypes.poetry_lock,
        filetypes.pyproject_toml
    ]
    
    for ft in file_types:
        assert isinstance(ft, str), f"File type {ft} is not a string"
        assert len(ft) > 0, f"File type {ft} is an empty string"


# Property 4: File type constants should be unique
def test_file_type_constants_are_unique():
    """Test that all file type constants have unique values"""
    
    file_types = [
        filetypes.requirements_txt,
        filetypes.conda_yml,
        filetypes.setup_cfg,
        filetypes.tox_ini,
        filetypes.pipfile,
        filetypes.pipfile_lock,
        filetypes.poetry_lock,
        filetypes.pyproject_toml
    ]
    
    # Check uniqueness
    assert len(file_types) == len(set(file_types)), \
        f"File type constants are not unique: {file_types}"


# Property 5: Valid file types should always result in a parser being assigned
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
def test_valid_file_type_always_has_parser(file_type):
    """Test that valid file types always result in a parser being assigned"""
    
    content = ""
    df = DependencyFile(content=content, file_type=file_type)
    
    # Should have a parser
    assert hasattr(df, 'parser'), f"DependencyFile with file_type={file_type} has no parser"
    assert df.parser is not None, f"DependencyFile with file_type={file_type} has None parser"


# Property 6: File type constant values should match expected file names
def test_file_type_values_match_expected_names():
    """Test that file type constant values match their expected file names"""
    
    expected_values = {
        filetypes.requirements_txt: "requirements.txt",
        filetypes.conda_yml: "conda.yml",
        filetypes.setup_cfg: "setup.cfg",
        filetypes.tox_ini: "tox.ini",
        filetypes.pipfile: "Pipfile",
        filetypes.pipfile_lock: "Pipfile.lock",
        filetypes.poetry_lock: "poetry.lock",
        filetypes.pyproject_toml: "pyproject.toml"
    }
    
    for file_type, expected_value in expected_values.items():
        assert file_type == expected_value, \
            f"File type constant value mismatch: {file_type} != {expected_value}"


# Property 7: Path endings should uniquely determine parser
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
def test_path_ending_determines_parser(path):
    """Test that file path endings uniquely determine the parser"""
    
    content = ""
    df = DependencyFile(content=content, path=path)
    
    # Should have a parser
    assert hasattr(df, 'parser'), f"DependencyFile with path={path} has no parser"
    assert df.parser is not None, f"DependencyFile with path={path} has None parser"
    
    # Parser class should be consistent for the same path
    df2 = DependencyFile(content=content, path=path)
    assert df.parser.__class__ == df2.parser.__class__, \
        f"Same path {path} resulted in different parsers"


if __name__ == "__main__":
    # Run all tests
    print("Running property-based tests for dparse.filetypes...")
    
    test_file_type_constants_are_strings()
    print("✓ All file type constants are strings")
    
    test_file_type_constants_are_unique()
    print("✓ All file type constants are unique")
    
    test_file_type_values_match_expected_names()
    print("✓ File type values match expected names")
    
    test_file_type_path_consistency()
    print("✓ File type to path consistency maintained")
    
    # Run hypothesis tests with more examples
    test_serialization_round_trip = settings(max_examples=100)(test_serialization_round_trip)
    test_valid_file_type_always_has_parser = settings(max_examples=100)(test_valid_file_type_always_has_parser)
    test_path_ending_determines_parser = settings(max_examples=100)(test_path_ending_determines_parser)
    
    test_serialization_round_trip()
    print("✓ Serialization round-trip preserves file_type")
    
    test_valid_file_type_always_has_parser()
    print("✓ Valid file types always have parsers")
    
    test_path_ending_determines_parser()
    print("✓ Path endings uniquely determine parser")
    
    print("\nAll tests passed!")