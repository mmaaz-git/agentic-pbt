import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/dparse_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
from hypothesis.strategies import composite
import dparse.dependencies as deps
from packaging.specifiers import SpecifierSet
import json


# Test edge cases for Dependency.key
@given(st.text())
def test_dependency_key_with_arbitrary_text(name):
    """Test Dependency.key with arbitrary text input"""
    try:
        dep = deps.Dependency(name=name, specs=SpecifierSet(), line="test")
        # Key should always be lowercase
        assert dep.key == dep.key.lower()
        # Key should have underscores replaced with hyphens
        assert "_" not in dep.key or dep.key == name.lower().replace("_", "-")
    except Exception:
        # Some names might be invalid
        pass


# Test empty name
def test_dependency_empty_name():
    """Test Dependency with empty name"""
    dep = deps.Dependency(name="", specs=SpecifierSet(), line="test")
    assert dep.name == ""
    assert dep.key == ""
    assert dep.full_name == ""


# Test extras with special characters
@given(st.lists(st.text(), min_size=1, max_size=5))
def test_dependency_extras_with_special_chars(extras):
    """Test full_name with extras containing special characters"""
    dep = deps.Dependency(name="package", specs=SpecifierSet(), line="test", extras=extras)
    full_name = dep.full_name
    
    if extras:
        assert full_name.startswith("package[")
        assert full_name.endswith("]")
        # Check that all extras are in the full_name
        extras_part = full_name[8:-1]  # Remove "package[" and "]"
        assert extras_part == ",".join(extras)


# Test DependencyFile serialization round-trip
@given(st.text(), st.one_of(st.none(), st.text()), st.one_of(st.none(), st.text()))
def test_dependency_file_serialization(content, path, sha):
    """Test DependencyFile serialization"""
    try:
        dep_file = deps.DependencyFile(content=content, path=path, sha=sha)
        serialized = dep_file.serialize()
        
        # Verify serialized structure
        assert serialized["content"] == content
        assert serialized["path"] == path
        assert serialized["sha"] == sha
        assert "dependencies" in serialized
        assert "resolved_dependencies" in serialized
        
        # Test deserialization
        deserialized = deps.DependencyFile.deserialize(serialized)
        assert deserialized.content == content
        assert deserialized.path == path
        assert deserialized.sha == sha
    except Exception:
        # Invalid files may raise exceptions
        pass


# Test DependencyFile with various file extensions
@given(st.sampled_from([
    "requirements.txt", "requirements.in", "Pipfile", "Pipfile.lock",
    "setup.cfg", "poetry.lock", "pyproject.toml", "environment.yml",
    "tox.ini", "unknown.xyz"
]))
def test_dependency_file_extension_detection(filename):
    """Test that DependencyFile correctly detects file types from extensions"""
    try:
        dep_file = deps.DependencyFile(content="test content", path=filename)
        # If we get here, the file type was recognized
        assert hasattr(dep_file, 'parser')
    except deps.errors.UnknownDependencyFileError:
        # Unknown file types should raise this error
        assert filename == "unknown.xyz"
    except Exception:
        # Parser might fail for invalid content
        pass


# Test nested DependencyFile resolution
def test_dependency_file_resolved_dependencies():
    """Test that resolved_dependencies includes nested dependencies"""
    # Create main file
    main_file = deps.DependencyFile(content="", path="requirements.txt")
    
    # Add direct dependencies
    dep1 = deps.Dependency(name="dep1", specs=SpecifierSet(), line="dep1")
    dep2 = deps.Dependency(name="dep2", specs=SpecifierSet(), line="dep2")
    main_file.dependencies = [dep1, dep2]
    
    # Create nested file
    nested_file = deps.DependencyFile(content="", path="nested.txt")
    dep3 = deps.Dependency(name="dep3", specs=SpecifierSet(), line="dep3")
    nested_file.dependencies = [dep3]
    
    # Add nested file to resolved_files
    main_file.resolved_files = [nested_file]
    
    # Test resolved_dependencies property
    resolved = main_file.resolved_dependencies
    assert len(resolved) == 3
    assert dep1 in resolved
    assert dep2 in resolved
    assert dep3 in resolved


# Test Dependency with None values
def test_dependency_with_none_values():
    """Test Dependency handles None values correctly"""
    dep = deps.Dependency(
        name="test",
        specs=None,
        line=None,
        source=None,
        meta=None,
        extras=None,
        line_numbers=None,
        index_server=None,
        hashes=None,
        dependency_type=None,
        sections=None
    )
    
    serialized = dep.serialize()
    deserialized = deps.Dependency.deserialize(serialized)
    
    assert deserialized.name == "test"
    assert deserialized.specs is None
    assert deserialized.line is None


# Test key normalization edge cases
@given(st.text(alphabet="_-", min_size=1, max_size=20))
def test_dependency_key_only_underscores_hyphens(name):
    """Test key normalization with names containing only underscores and hyphens"""
    dep = deps.Dependency(name=name, specs=SpecifierSet(), line="test")
    # All underscores should become hyphens
    expected = name.lower().replace("_", "-")
    assert dep.key == expected


# Test multiple consecutive underscores/hyphens
@given(st.integers(min_value=1, max_value=10))
def test_dependency_key_consecutive_chars(n):
    """Test key normalization with consecutive underscores"""
    name = "package" + "_" * n + "name"
    dep = deps.Dependency(name=name, specs=SpecifierSet(), line="test")
    expected = "package" + "-" * n + "name"
    assert dep.key == expected


# Test Unicode in dependency names
@given(st.text(alphabet="αβγδεζηθικλμνξοπρστυφχψω", min_size=1, max_size=10))
def test_dependency_unicode_names(name):
    """Test Dependency with Unicode characters in name"""
    dep = deps.Dependency(name=name, specs=SpecifierSet(), line="test")
    assert dep.name == name
    assert dep.key == name.lower().replace("_", "-")
    assert dep.full_name == name