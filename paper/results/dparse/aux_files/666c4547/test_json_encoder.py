import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/dparse_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import dparse.dependencies as deps
from packaging.specifiers import SpecifierSet
import json


# Test DparseJSONEncoder with various data types
@given(st.sets(st.text(min_size=1, max_size=10)))
def test_json_encoder_with_sets(test_set):
    """Test that DparseJSONEncoder correctly converts sets to lists"""
    encoder = deps.DparseJSONEncoder()
    
    # Encode the set
    json_str = json.dumps({"test": test_set}, cls=deps.DparseJSONEncoder)
    decoded = json.loads(json_str)
    
    # Sets should become lists
    assert isinstance(decoded["test"], list)
    assert set(decoded["test"]) == test_set


# Test with SpecifierSet
@given(st.lists(st.sampled_from(["==", "!=", "<=", ">=", "<", ">", "~=", "==="]), min_size=1, max_size=3))
def test_json_encoder_with_specifier_sets(operators):
    """Test that DparseJSONEncoder correctly handles SpecifierSet objects"""
    specs = []
    for i, op in enumerate(operators):
        specs.append(f"{op}{i}.0.0")
    
    spec_set = SpecifierSet(",".join(specs))
    
    # Create a dependency with the SpecifierSet
    dep = deps.Dependency(name="test", specs=spec_set, line="test")
    
    # Serialize and deserialize
    json_str = json.dumps(dep.serialize(), cls=deps.DparseJSONEncoder)
    decoded = json.loads(json_str)
    
    # The specs should be serialized as a string
    assert isinstance(decoded["specs"], str)
    assert decoded["specs"] == str(spec_set)


# Test complex nested structures
@given(
    st.dictionaries(
        st.text(min_size=1, max_size=10),
        st.one_of(
            st.sets(st.integers()),
            st.lists(st.sets(st.text(max_size=5))),
            st.dictionaries(st.text(max_size=5), st.sets(st.integers()))
        ),
        max_size=5
    )
)
def test_json_encoder_nested_structures(data):
    """Test DparseJSONEncoder with nested sets in complex structures"""
    json_str = json.dumps(data, cls=deps.DparseJSONEncoder)
    decoded = json.loads(json_str)
    
    # All sets should have been converted to lists
    def check_no_sets(obj):
        if isinstance(obj, dict):
            for value in obj.values():
                check_no_sets(value)
        elif isinstance(obj, list):
            for item in obj:
                check_no_sets(item)
        else:
            assert not isinstance(obj, set)
    
    check_no_sets(decoded)


# Test Dependency with sets in meta field
@given(st.dictionaries(st.text(min_size=1, max_size=10), st.sets(st.text(max_size=10)), max_size=3))
def test_dependency_meta_with_sets(meta_with_sets):
    """Test Dependency serialization when meta contains sets"""
    dep = deps.Dependency(
        name="test",
        specs=SpecifierSet(),
        line="test",
        meta=meta_with_sets
    )
    
    # This should work with the custom encoder
    json_str = json.dumps(dep.serialize(), cls=deps.DparseJSONEncoder)
    decoded = json.loads(json_str)
    
    # Meta values that were sets should now be lists
    for key, value in meta_with_sets.items():
        assert set(decoded["meta"][key]) == value


# Test DependencyFile.json() method
def test_dependency_file_json_method():
    """Test the json() method of DependencyFile"""
    dep_file = deps.DependencyFile(content="test", path="requirements.txt")
    dep1 = deps.Dependency(name="dep1", specs=SpecifierSet(">=1.0.0"), line="dep1>=1.0.0")
    dep2 = deps.Dependency(name="dep2", specs=SpecifierSet("<2.0.0"), line="dep2<2.0.0")
    dep_file.dependencies = [dep1, dep2]
    
    # Call the json() method
    json_str = dep_file.json()
    
    # Should be valid JSON
    decoded = json.loads(json_str)
    assert decoded["content"] == "test"
    assert decoded["path"] == "requirements.txt"
    assert len(decoded["dependencies"]) == 2


# Test edge case: circular reference in meta
def test_dependency_circular_reference():
    """Test what happens with circular references in meta"""
    meta = {}
    meta["self"] = meta  # Circular reference
    
    dep = deps.Dependency(
        name="test",
        specs=SpecifierSet(),
        line="test",
        meta=meta
    )
    
    # This should raise an error due to circular reference
    try:
        json.dumps(dep.serialize(), cls=deps.DparseJSONEncoder)
        assert False, "Should have raised an error for circular reference"
    except (ValueError, RecursionError):
        pass  # Expected


# Test extras as non-list
def test_dependency_extras_non_list():
    """Test Dependency behavior when extras is not a list"""
    # According to the code, extras is expected to be a list
    # Let's test what happens with other types
    
    # Test with string
    dep = deps.Dependency(name="test", specs=SpecifierSet(), line="test", extras="extra")
    # This might work or fail, let's see
    try:
        full_name = dep.full_name
        # If it works, check the format
        if full_name != "test":
            assert "[" in full_name and "]" in full_name
    except TypeError:
        pass  # Expected if it doesn't handle non-list extras
    
    # Test with None (already tested in edge cases)
    dep = deps.Dependency(name="test", specs=SpecifierSet(), line="test", extras=None)
    assert dep.full_name == "test"  # Should just return the name