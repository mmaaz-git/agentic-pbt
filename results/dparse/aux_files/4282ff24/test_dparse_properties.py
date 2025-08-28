#!/usr/bin/env /root/hypothesis-llm/envs/dparse_env/bin/python3

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/dparse_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
from hypothesis.strategies import text, lists, sets, dictionaries, one_of, none, sampled_from, integers, booleans
import json
import re
from packaging.specifiers import SpecifierSet
from dparse.dependencies import Dependency, DependencyFile, DparseJSONEncoder
from dparse.parser import Parser
from dparse import filetypes


# Strategy for generating valid package names
package_name_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters="_-"),
    min_size=1,
    max_size=50
).filter(lambda x: x and not x[0].isdigit() and not x.startswith("-"))

# Strategy for generating valid specifier sets
specifier_strategy = st.one_of(
    st.just(SpecifierSet()),
    st.sampled_from([
        SpecifierSet(">=1.0.0"),
        SpecifierSet("==2.3.4"),
        SpecifierSet("<3.0"),
        SpecifierSet("~=1.2.0"),
        SpecifierSet("!=1.5"),
        SpecifierSet(">=1.0,<2.0")
    ])
)

# Strategy for generating extras
extras_strategy = st.lists(
    st.text(alphabet=st.characters(whitelist_categories=("Ll",), whitelist_characters="_-"), min_size=1, max_size=20),
    min_size=0,
    max_size=5
)

# Strategy for line content
line_strategy = st.text(min_size=0, max_size=200)

# Strategy for dependency types
dependency_type_strategy = st.sampled_from([
    filetypes.requirements_txt,
    filetypes.conda_yml,
    filetypes.pipfile,
    filetypes.pipfile_lock,
    filetypes.poetry_lock,
    filetypes.pyproject_toml,
    filetypes.setup_cfg,
    filetypes.tox_ini
])


@given(package_name_strategy)
def test_dependency_key_property(name):
    """Test that Dependency.key is always lowercase with underscores replaced by hyphens"""
    dep = Dependency(
        name=name,
        specs=SpecifierSet(),
        line=name
    )
    
    # Property from dependencies.py line 28
    expected_key = name.lower().replace("_", "-")
    assert dep.key == expected_key


@given(package_name_strategy, extras_strategy)
def test_dependency_full_name_property(name, extras):
    """Test that full_name correctly combines name and extras"""
    dep = Dependency(
        name=name,
        specs=SpecifierSet(),
        line=name,
        extras=extras
    )
    
    # Property from dependencies.py lines 85-87
    if extras:
        expected = f"{name}[{','.join(extras)}]"
    else:
        expected = name
    
    assert dep.full_name == expected


@given(
    package_name_strategy,
    specifier_strategy,
    line_strategy,
    st.text(min_size=0, max_size=20),  # source
    st.dictionaries(st.text(max_size=20), st.text(max_size=100), max_size=5),  # meta
    extras_strategy,
    st.one_of(st.none(), st.lists(st.integers(min_value=0, max_value=1000), min_size=1, max_size=5)),  # line_numbers
    st.one_of(st.none(), st.text(min_size=0, max_size=100)),  # index_server
    st.lists(st.text(min_size=0, max_size=100), min_size=0, max_size=5),  # hashes
    st.one_of(st.none(), dependency_type_strategy),  # dependency_type
    st.one_of(st.none(), st.lists(st.text(min_size=1, max_size=20), min_size=0, max_size=3))  # sections
)
def test_dependency_serialize_deserialize_roundtrip(
    name, specs, line, source, meta, extras, line_numbers, 
    index_server, hashes, dependency_type, sections
):
    """Test that serialize/deserialize is a proper round-trip"""
    original = Dependency(
        name=name,
        specs=specs,
        line=line,
        source=source,
        meta=meta,
        extras=extras,
        line_numbers=line_numbers,
        index_server=index_server,
        hashes=tuple(hashes),
        dependency_type=dependency_type,
        sections=sections
    )
    
    # Serialize and deserialize
    serialized = original.serialize()
    
    # Need to convert specs to string for serialization
    serialized_json = json.dumps(serialized, cls=DparseJSONEncoder)
    deserialized_dict = json.loads(serialized_json)
    
    # Convert specs back to SpecifierSet
    if isinstance(deserialized_dict['specs'], str):
        deserialized_dict['specs'] = SpecifierSet(deserialized_dict['specs'])
    
    restored = Dependency.deserialize(deserialized_dict)
    
    # Verify all fields match
    assert restored.name == original.name
    assert restored.key == original.key
    assert str(restored.specs) == str(original.specs)
    assert restored.line == original.line
    assert restored.source == original.source
    assert restored.meta == original.meta
    assert restored.extras == original.extras
    assert restored.line_numbers == original.line_numbers
    assert restored.index_server == original.index_server
    assert set(restored.hashes) == set(original.hashes) if original.hashes else restored.hashes == original.hashes
    assert restored.dependency_type == original.dependency_type
    assert restored.sections == original.sections


@given(st.text(min_size=0, max_size=200))
def test_parse_hashes_extraction(line):
    """Test that parse_hashes correctly extracts hash patterns"""
    # Inject some valid hash patterns
    hash_patterns = [
        "--hash=sha256:abc123def456",
        "--hash sha512:1234567890ab",
        "--hash md5:deadbeef"
    ]
    
    # Build a line with hashes
    test_line = line
    injected_hashes = []
    for pattern in hash_patterns:
        if st.booleans().example():
            test_line += f" {pattern}"
            injected_hashes.append(pattern)
    
    # Parse hashes
    cleaned_line, extracted = Parser.parse_hashes(test_line)
    
    # Verify that all injected hashes were extracted
    for hash_val in injected_hashes:
        assert hash_val in extracted
    
    # Verify that hashes are removed from the cleaned line
    for hash_val in extracted:
        assert hash_val not in cleaned_line


@given(st.text(alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd"), whitelist_characters=".-/:"), 
              min_size=1, max_size=100))
def test_parse_index_server_normalization(url):
    """Test that parse_index_server normalizes URLs with trailing slash"""
    assume(not url.startswith(" ") and not url.endswith(" "))
    
    # Create various index server lines
    lines = [
        f"-i {url}",
        f"--index-url {url}",
        f"--index-url={url}",
        f"-i={url}"
    ]
    
    for line in lines:
        result = Parser.parse_index_server(line)
        
        if result is not None:
            # Property from parser.py line 189: should end with /
            assert result.endswith("/")
            
            # Should contain the original URL
            if url.endswith("/"):
                assert result == url
            else:
                assert result == url + "/"


@given(st.text(min_size=0, max_size=100))
def test_hash_regex_pattern(text):
    """Test the HASH_REGEX pattern matching"""
    from dparse.regex import HASH_REGEX
    
    # Test valid patterns
    valid_patterns = [
        "--hash=sha256:abc123",
        "--hash md5:deadbeef",
        "--hash sha512:1234567890abcdef"
    ]
    
    for pattern in valid_patterns:
        test_text = text + pattern
        matches = re.findall(HASH_REGEX, test_text)
        assert pattern in matches
        
    # Test that random text doesn't match accidentally
    if "--hash" not in text and not re.search(r"\w+:\w+", text):
        matches = re.findall(HASH_REGEX, text)
        assert len(matches) == 0


@given(
    st.text(min_size=0, max_size=1000),  # content
    st.one_of(st.none(), st.text(min_size=1, max_size=100)),  # path
    st.one_of(st.none(), st.text(min_size=0, max_size=64)),  # sha
    st.one_of(st.none(), dependency_type_strategy)  # file_type
)
def test_dependency_file_initialization(content, path, sha, file_type):
    """Test that DependencyFile can be initialized and identifies parser correctly"""
    
    # Skip cases where no parser can be determined
    if file_type is None and path is None:
        assume(False)
    
    # Adjust path to match expected file types if needed
    if path and file_type:
        if file_type == filetypes.requirements_txt and not path.endswith((".txt", ".in")):
            path = path + ".txt"
        elif file_type == filetypes.pipfile and not path.endswith("Pipfile"):
            path = "Pipfile"
        elif file_type == filetypes.pipfile_lock and not path.endswith("Pipfile.lock"):
            path = "Pipfile.lock"
        elif file_type == filetypes.poetry_lock and not path.endswith("poetry.lock"):
            path = "poetry.lock"
        elif file_type == filetypes.pyproject_toml and not path.endswith("pyproject.toml"):
            path = "pyproject.toml"
        elif file_type == filetypes.conda_yml and not path.endswith(".yml"):
            path = path + ".yml"
        elif file_type == filetypes.tox_ini and not path.endswith(".ini"):
            path = path + ".ini"
        elif file_type == filetypes.setup_cfg and not path.endswith("setup.cfg"):
            path = "setup.cfg"
    
    try:
        dep_file = DependencyFile(
            content=content,
            path=path,
            sha=sha,
            file_type=file_type
        )
        
        # Should have a parser
        assert dep_file.parser is not None
        
        # Dependencies list should be initialized
        assert isinstance(dep_file.dependencies, list)
        assert isinstance(dep_file.resolved_files, list)
        
    except Exception as e:
        # Only UnknownDependencyFileError is expected for unrecognized types
        from dparse.errors import UnknownDependencyFileError
        assert isinstance(e, UnknownDependencyFileError)


if __name__ == "__main__":
    import pytest
    
    # Run with increased examples for better coverage
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])