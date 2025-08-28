#!/usr/bin/env python3
import sys
import traceback
sys.path.insert(0, '/root/hypothesis-llm/envs/dparse_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, Verbosity
from hypothesis import seed
import re
import json
from pathlib import PurePath

import dparse.parser as parser_module
from dparse.parser import Parser, RequirementsTXTLineParser
from dparse.dependencies import Dependency, DependencyFile, DparseJSONEncoder
from dparse.regex import HASH_REGEX
from dparse import filetypes
from packaging.specifiers import SpecifierSet


def run_test(test_func, test_name):
    print(f"\nTesting: {test_name}")
    try:
        # Run with a fixed seed for reproducibility
        test_func = seed(12345)(test_func)
        test_func = settings(max_examples=100, verbosity=Verbosity.verbose)(test_func)
        test_func()
        print(f"✓ {test_name} passed")
        return True
    except Exception as e:
        print(f"✗ {test_name} failed")
        print(f"  Error: {e}")
        traceback.print_exc()
        return False


# Define strategies
package_name = st.text(
    alphabet=st.characters(min_codepoint=33, max_codepoint=126, blacklist_characters="#[]()<>=!/\\@"),
    min_size=1,
    max_size=50
).filter(lambda x: not x.startswith('-') and not x.endswith('-'))

version_spec = st.text(
    alphabet="0123456789.*<>=!~,",
    min_size=0,
    max_size=20
)

hash_algo = st.sampled_from(['sha256', 'sha384', 'sha512', 'md5'])
hash_value = st.text(alphabet='0123456789abcdef', min_size=32, max_size=128)


# Test 1: Hash removal
@given(st.text())
def test_parse_hashes_removes_all_hashes(line):
    cleaned_line, hashes = Parser.parse_hashes(line)
    assert not re.search(HASH_REGEX, cleaned_line)


# Test 2: Hash extraction
@given(hash_algo, hash_value)
def test_parse_hashes_extraction(algo, value):
    line = f"package==1.0.0 --hash={algo}:{value}"
    cleaned_line, hashes = Parser.parse_hashes(line)
    assert f"--hash={algo}:{value}" in hashes
    assert "package==1.0.0" == cleaned_line.strip()


# Test 3: Multiple hashes
@given(st.lists(st.tuples(hash_algo, hash_value), min_size=1, max_size=5))
def test_parse_hashes_multiple(hash_pairs):
    base = "package==1.0.0"
    hash_strings = [f"--hash={algo}:{value}" for algo, value in hash_pairs]
    line = f"{base} {' '.join(hash_strings)}"
    
    cleaned_line, hashes = Parser.parse_hashes(line)
    assert cleaned_line.strip() == base
    assert len(hashes) == len(hash_pairs)
    for hash_str in hash_strings:
        assert hash_str in hashes


# Test 4: Index server trailing slash
@given(st.text(min_size=1))
def test_parse_index_server_trailing_slash_invariant(url):
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


# Test 5: Dependency key normalization
@given(package_name)
def test_dependency_key_normalization(name):
    dep = Dependency(
        name=name,
        specs=SpecifierSet(),
        line=name
    )
    
    expected_key = name.lower().replace("_", "-")
    assert dep.key == expected_key


# Test 6: Dependency full name with extras
@given(package_name, st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=5))
def test_dependency_full_name_with_extras(name, extras):
    dep = Dependency(
        name=name,
        specs=SpecifierSet(),
        line=name,
        extras=extras
    )
    
    expected = f"{name}[{','.join(extras)}]"
    assert dep.full_name == expected


# Test 7: Resolve file removes flags
@given(st.text(min_size=1), st.text(min_size=1))
def test_resolve_file_removes_requirement_flags(base_path, req_path):
    assume(not req_path.startswith('/'))
    
    line1 = f"-r {req_path}"
    line2 = f"--requirement {req_path}"
    
    result1 = Parser.resolve_file(base_path, line1)
    result2 = Parser.resolve_file(base_path, line2)
    
    assert result1 == result2
    assert "-r" not in result1
    assert "--requirement" not in result2


# Test 8: File type detection
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
    path, expected_parser = path_and_parser
    
    dep_file = DependencyFile(
        content="",
        path=f"/some/path/{path}"
    )
    
    assert dep_file.parser.__class__.__name__ == expected_parser


if __name__ == "__main__":
    print("=" * 60)
    print("Running Property-Based Tests for dparse.parser")
    print("=" * 60)
    
    tests = [
        (test_parse_hashes_removes_all_hashes, "parse_hashes removes all hashes"),
        (test_parse_hashes_extraction, "parse_hashes extraction"),
        (test_parse_hashes_multiple, "parse_hashes multiple hashes"),
        (test_parse_index_server_trailing_slash_invariant, "parse_index_server trailing slash invariant"),
        (test_dependency_key_normalization, "Dependency key normalization"),
        (test_dependency_full_name_with_extras, "Dependency full_name with extras"),
        (test_resolve_file_removes_requirement_flags, "resolve_file removes requirement flags"),
        (test_dependency_file_parser_detection_by_path, "DependencyFile parser detection by path"),
    ]
    
    passed = 0
    failed = 0
    
    for test_func, test_name in tests:
        if run_test(test_func, test_name):
            passed += 1
        else:
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)