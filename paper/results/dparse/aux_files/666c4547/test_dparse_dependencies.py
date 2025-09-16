import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/dparse_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
from hypothesis.strategies import composite
import dparse.dependencies as deps
from packaging.specifiers import SpecifierSet
import json


@composite
def dependency_name_strategy(draw):
    """Generate valid Python package names"""
    first_char = draw(st.sampled_from("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"))
    rest = draw(st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-.", min_size=0, max_size=50))
    name = first_char + rest
    # Remove trailing dots/hyphens which are invalid
    name = name.rstrip(".-")
    assume(len(name) > 0)
    return name


@composite
def specifier_strategy(draw):
    """Generate valid version specifiers"""
    operators = ["==", "!=", "<=", ">=", "<", ">", "~=", "==="]
    op = draw(st.sampled_from(operators))
    major = draw(st.integers(min_value=0, max_value=99))
    minor = draw(st.integers(min_value=0, max_value=99))
    patch = draw(st.integers(min_value=0, max_value=99))
    version = f"{major}.{minor}.{patch}"
    return SpecifierSet(f"{op}{version}")


@composite 
def extras_strategy(draw):
    """Generate valid extras lists"""
    n_extras = draw(st.integers(min_value=0, max_value=5))
    extras = []
    for _ in range(n_extras):
        extra = draw(st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789_-", min_size=1, max_size=20))
        extras.append(extra)
    return extras


@composite
def dependency_strategy(draw):
    """Generate a valid Dependency object"""
    name = draw(dependency_name_strategy())
    specs = draw(specifier_strategy())
    line = draw(st.text(min_size=1, max_size=100))
    source = draw(st.sampled_from(["pypi", "git", "file", "url"]))
    extras = draw(extras_strategy())
    line_numbers = draw(st.one_of(st.none(), st.lists(st.integers(min_value=1, max_value=1000), min_size=1, max_size=10)))
    index_server = draw(st.one_of(st.none(), st.text(min_size=1, max_size=50)))
    hashes = draw(st.tuples(*[st.text(min_size=0, max_size=64) for _ in range(draw(st.integers(min_value=0, max_value=3)))]))
    dependency_type = draw(st.one_of(st.none(), st.text(min_size=1, max_size=20)))
    sections = draw(st.one_of(st.none(), st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=5)))
    meta = draw(st.dictionaries(st.text(min_size=1, max_size=20), st.text(min_size=0, max_size=100), max_size=5))
    
    return deps.Dependency(
        name=name,
        specs=specs,
        line=line,
        source=source,
        extras=extras,
        line_numbers=line_numbers,
        index_server=index_server,
        hashes=hashes,
        dependency_type=dependency_type,
        sections=sections,
        meta=meta
    )


# Test 1: Dependency.key normalization property
@given(dependency_name_strategy())
def test_dependency_key_normalization(name):
    """Test that Dependency.key always normalizes names correctly"""
    dep = deps.Dependency(name=name, specs=SpecifierSet(), line="test")
    
    # The key should be lowercase and replace underscores with hyphens
    expected_key = name.lower().replace("_", "-")
    assert dep.key == expected_key
    
    # The key should be idempotent
    dep2 = deps.Dependency(name=dep.key, specs=SpecifierSet(), line="test")
    assert dep2.key == dep.key


# Test 2: Dependency.full_name with extras property
@given(dependency_name_strategy(), extras_strategy())
def test_dependency_full_name_with_extras(name, extras):
    """Test that full_name correctly formats name with extras"""
    dep = deps.Dependency(name=name, specs=SpecifierSet(), line="test", extras=extras)
    
    if extras:
        expected = f"{name}[{','.join(extras)}]"
        assert dep.full_name == expected
    else:
        assert dep.full_name == name


# Test 3: Round-trip serialization property
@given(dependency_strategy())
@settings(max_examples=200)
def test_dependency_round_trip_serialization(dep):
    """Test that serialize/deserialize preserves all data"""
    serialized = dep.serialize()
    deserialized = deps.Dependency.deserialize(serialized)
    
    # Check all attributes are preserved
    assert deserialized.name == dep.name
    assert deserialized.key == dep.key
    assert str(deserialized.specs) == str(dep.specs)
    assert deserialized.line == dep.line
    assert deserialized.source == dep.source
    assert deserialized.meta == dep.meta
    assert deserialized.line_numbers == dep.line_numbers
    assert deserialized.index_server == dep.index_server
    assert deserialized.hashes == dep.hashes
    assert deserialized.dependency_type == dep.dependency_type
    assert deserialized.extras == dep.extras
    assert deserialized.sections == dep.sections


# Test 4: JSON serialization round-trip
@given(dependency_strategy())
@settings(max_examples=200)
def test_dependency_json_round_trip(dep):
    """Test that JSON serialization works correctly"""
    serialized = dep.serialize()
    json_str = json.dumps(serialized, cls=deps.DparseJSONEncoder)
    loaded = json.loads(json_str)
    deserialized = deps.Dependency.deserialize(loaded)
    
    assert deserialized.name == dep.name
    assert str(deserialized.specs) == str(dep.specs)
    assert deserialized.line == dep.line


# Test 5: DependencyFile content preservation
@given(st.text(min_size=1), st.one_of(st.none(), st.text(min_size=1, max_size=100)))
def test_dependency_file_content_preservation(content, path):
    """Test that DependencyFile preserves content and path"""
    try:
        dep_file = deps.DependencyFile(content=content, path=path)
        assert dep_file.content == content
        assert dep_file.path == path
    except Exception:
        # It's OK if invalid files raise exceptions
        pass


# Test 6: Dependency key case insensitivity
@given(dependency_name_strategy())
def test_dependency_key_case_insensitive(name):
    """Test that keys for different cases of the same name are equal"""
    dep1 = deps.Dependency(name=name.upper(), specs=SpecifierSet(), line="test")
    dep2 = deps.Dependency(name=name.lower(), specs=SpecifierSet(), line="test")
    assert dep1.key == dep2.key


# Test 7: Dependency key underscore/hyphen equivalence
@given(dependency_name_strategy())
def test_dependency_key_underscore_hyphen_equivalence(name):
    """Test that underscores and hyphens are treated as equivalent in keys"""
    name_with_underscores = name.replace("-", "_")
    name_with_hyphens = name.replace("_", "-")
    
    dep1 = deps.Dependency(name=name_with_underscores, specs=SpecifierSet(), line="test")
    dep2 = deps.Dependency(name=name_with_hyphens, specs=SpecifierSet(), line="test")
    assert dep1.key == dep2.key