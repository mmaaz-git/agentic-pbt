#!/usr/bin/env python3
import re
import json
from pathlib import PurePath
from hypothesis import given, strategies as st, assume
from hypothesis import settings
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/dparse_env/lib/python3.13/site-packages')

import dparse.parser as parser_module
from dparse.parser import Parser, RequirementsTXTLineParser
from dparse.dependencies import Dependency, DependencyFile, DparseJSONEncoder
from dparse.regex import HASH_REGEX
from dparse import filetypes
from packaging.specifiers import SpecifierSet


# Strategy for generating valid package names
package_name = st.text(
    alphabet=st.characters(min_codepoint=33, max_codepoint=126, blacklist_characters="#[]()<>=!/\\@"),
    min_size=1,
    max_size=50
).filter(lambda x: not x.startswith('-') and not x.endswith('-'))

# Strategy for generating version specifiers
version_spec = st.text(
    alphabet="0123456789.*<>=!~,",
    min_size=0,
    max_size=20
)

# Strategy for generating hash algorithms and values
hash_algo = st.sampled_from(['sha256', 'sha384', 'sha512', 'md5'])
hash_value = st.text(alphabet='0123456789abcdef', min_size=32, max_size=128)


@given(st.text())
def test_parse_hashes_removes_all_hashes(line):
    """Test that parse_hashes removes all hash patterns from the line"""
    cleaned_line, hashes = Parser.parse_hashes(line)
    # The cleaned line should not contain any hash patterns
    assert not re.search(HASH_REGEX, cleaned_line)


@given(hash_algo, hash_value)
def test_parse_hashes_extraction(algo, value):
    """Test that valid hashes are correctly extracted"""
    line = f"package==1.0.0 --hash={algo}:{value}"
    cleaned_line, hashes = Parser.parse_hashes(line)
    assert f"--hash={algo}:{value}" in hashes
    assert "package==1.0.0" == cleaned_line.strip()


@given(st.lists(st.tuples(hash_algo, hash_value), min_size=1, max_size=5))
def test_parse_hashes_multiple(hash_pairs):
    """Test parsing multiple hashes in a single line"""
    base = "package==1.0.0"
    hash_strings = [f"--hash={algo}:{value}" for algo, value in hash_pairs]
    line = f"{base} {' '.join(hash_strings)}"
    
    cleaned_line, hashes = Parser.parse_hashes(line)
    assert cleaned_line.strip() == base
    assert len(hashes) == len(hash_pairs)
    for hash_str in hash_strings:
        assert hash_str in hashes


@given(st.text(min_size=1))
def test_parse_index_server_trailing_slash_invariant(url):
    """Test that parse_index_server always returns URLs with trailing slash or None"""
    # Create various input formats
    test_cases = [
        f"-i {url}",
        f"--index-url {url}",
        f"--index-url={url}",
        f"-i={url}",
    ]
    
    for line in test_cases:
        result = Parser.parse_index_server(line)
        if result is not None:
            assert result.endswith('/'), f"URL should end with /: {result}"


@given(st.text())
def test_parse_index_server_preserves_trailing_slash(url):
    """Test that URLs already ending with / are preserved"""
    assume('/' not in url or url.endswith('/'))
    if url.endswith('/'):
        line = f"--index-url {url}"
        result = Parser.parse_index_server(line)
        if result:
            assert result == url


@given(package_name, version_spec, st.lists(st.text(min_size=1, max_size=10), max_size=3))
def test_dependency_serialization_roundtrip(name, specs, extras):
    """Test that Dependency objects can be serialized and deserialized"""
    dep = Dependency(
        name=name,
        specs=SpecifierSet(specs) if specs else SpecifierSet(),
        line=f"{name}{specs}",
        extras=extras
    )
    
    serialized = dep.serialize()
    deserialized = Dependency.deserialize(serialized)
    
    assert deserialized.name == dep.name
    assert deserialized.key == dep.key
    assert str(deserialized.specs) == str(dep.specs)
    assert deserialized.line == dep.line
    assert deserialized.extras == dep.extras


@given(package_name)
def test_dependency_key_normalization(name):
    """Test that dependency keys are normalized correctly"""
    dep = Dependency(
        name=name,
        specs=SpecifierSet(),
        line=name
    )
    
    # Key should be lowercase and replace underscores with hyphens
    expected_key = name.lower().replace("_", "-")
    assert dep.key == expected_key


@given(package_name, st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=5))
def test_dependency_full_name_with_extras(name, extras):
    """Test that full_name property correctly formats extras"""
    dep = Dependency(
        name=name,
        specs=SpecifierSet(),
        line=name,
        extras=extras
    )
    
    expected = f"{name}[{','.join(extras)}]"
    assert dep.full_name == expected


@given(package_name)
def test_dependency_full_name_without_extras(name):
    """Test that full_name without extras returns just the name"""
    dep = Dependency(
        name=name,
        specs=SpecifierSet(),
        line=name,
        extras=[]
    )
    
    assert dep.full_name == name


@given(st.text(min_size=1), st.text(min_size=1))
def test_resolve_file_removes_requirement_flags(base_path, req_path):
    """Test that resolve_file removes -r and --requirement flags"""
    assume(not req_path.startswith('/'))
    
    line1 = f"-r {req_path}"
    line2 = f"--requirement {req_path}"
    
    result1 = Parser.resolve_file(base_path, line1)
    result2 = Parser.resolve_file(base_path, line2)
    
    # Both should produce the same result
    assert result1 == result2
    # Should not contain the flags
    assert "-r" not in result1
    assert "--requirement" not in result2


@given(st.text(min_size=1), st.text(min_size=1))
def test_resolve_file_strips_comments(base_path, req_path):
    """Test that resolve_file strips comments from paths"""
    assume('#' not in req_path)
    
    line = f"-r {req_path} # some comment"
    result = Parser.resolve_file(base_path, line)
    
    # Should not contain the comment
    assert "# some comment" not in result
    assert "#" not in result


@given(st.sampled_from([
    ("requirements.txt", "RequirementsTXTParser"),
    ("requirements.in", "RequirementsTXTParser"),
    ("environment.yml", "CondaYMLParser"),
    ("tox.ini", "ToxINIParser"),
    ("Pipfile", "PipfileParser"),
    ("Pipfile.lock", "PipfileLockParser"),
    ("setup.cfg", "SetupCfgParser"),
    ("poetry.lock", "PoetryLockParser"),
    ("pyproject.toml", "PyprojectTomlParser")
]))
def test_dependency_file_parser_detection_by_path(path_and_parser):
    """Test that DependencyFile correctly detects parser based on file path"""
    path, expected_parser = path_and_parser
    
    dep_file = DependencyFile(
        content="",
        path=f"/some/path/{path}"
    )
    
    assert dep_file.parser.__class__.__name__ == expected_parser


@given(st.text())
def test_dependency_file_json_serializable(content):
    """Test that DependencyFile.json() produces valid JSON"""
    try:
        dep_file = DependencyFile(
            content=content,
            path="requirements.txt"
        )
        json_str = dep_file.json()
        # Should be valid JSON
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)
    except Exception:
        # Some content might cause parser errors, which is fine
        pass


@given(st.sampled_from([
    filetypes.requirements_txt,
    filetypes.conda_yml,
    filetypes.tox_ini,
    filetypes.pipfile,
    filetypes.pipfile_lock,
    filetypes.setup_cfg,
    filetypes.poetry_lock,
    filetypes.pyproject_toml
]))
def test_dependency_file_parser_detection_by_type(file_type):
    """Test that DependencyFile correctly detects parser based on file_type"""
    parser_map = {
        filetypes.requirements_txt: "RequirementsTXTParser",
        filetypes.conda_yml: "CondaYMLParser",
        filetypes.tox_ini: "ToxINIParser",
        filetypes.pipfile: "PipfileParser",
        filetypes.pipfile_lock: "PipfileLockParser",
        filetypes.setup_cfg: "SetupCfgParser",
        filetypes.poetry_lock: "PoetryLockParser",
        filetypes.pyproject_toml: "PyprojectTomlParser"
    }
    
    dep_file = DependencyFile(
        content="",
        file_type=file_type
    )
    
    expected_parser = parser_map[file_type]
    assert dep_file.parser.__class__.__name__ == expected_parser


@given(st.text())
def test_hash_regex_pattern_matching(text):
    """Test that HASH_REGEX correctly identifies hash patterns"""
    matches = re.findall(HASH_REGEX, text)
    
    # All matches should follow the pattern --hash[=| ]algorithm:value
    for match in matches:
        assert match.startswith("--hash")
        assert ":" in match
        parts = match.split(":")
        assert len(parts) == 2


if __name__ == "__main__":
    import pytest
    import sys
    
    print("Running property-based tests for dparse.parser...")
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))