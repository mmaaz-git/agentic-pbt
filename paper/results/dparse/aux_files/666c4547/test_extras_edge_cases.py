import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/dparse_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import dparse.dependencies as deps
from packaging.specifiers import SpecifierSet


# Test extras as string (should be a list according to the constructor)
def test_extras_as_string():
    """Test what happens when extras is a string instead of list"""
    dep = deps.Dependency(name="test", specs=SpecifierSet(), line="test", extras="security")
    
    # The full_name property assumes extras is iterable and joinable
    # This should cause an issue since string.join() on a string gives unexpected results
    full_name = dep.full_name
    
    # When extras="security" and we do ",".join("security"), we get "s,e,c,u,r,i,t,y"
    print(f"Full name with string extras: {full_name}")
    assert full_name == "test[s,e,c,u,r,i,t,y]"


# Test extras as single-character string
def test_extras_single_char_string():
    """Test extras with single character string"""
    dep = deps.Dependency(name="pkg", specs=SpecifierSet(), line="test", extras="a")
    assert dep.full_name == "pkg[a]"


# Test extras as tuple (should work since it's iterable)
def test_extras_as_tuple():
    """Test extras as tuple instead of list"""
    dep = deps.Dependency(name="test", specs=SpecifierSet(), line="test", extras=("extra1", "extra2"))
    assert dep.full_name == "test[extra1,extra2]"


# Test extras with empty string in list
def test_extras_with_empty_string():
    """Test extras list containing empty string"""
    dep = deps.Dependency(name="test", specs=SpecifierSet(), line="test", extras=["", "extra", ""])
    assert dep.full_name == "test[,extra,]"


# Test extras with commas in the extra names
def test_extras_with_commas():
    """Test extras containing commas - this could break parsing"""
    dep = deps.Dependency(name="test", specs=SpecifierSet(), line="test", extras=["extra,with,comma"])
    # This creates ambiguous format: test[extra,with,comma] - is it 1 or 3 extras?
    assert dep.full_name == "test[extra,with,comma]"


# Test extras with brackets
def test_extras_with_brackets():
    """Test extras containing brackets - could break format"""
    dep = deps.Dependency(name="test", specs=SpecifierSet(), line="test", extras=["[extra]", "normal"])
    # This creates malformed format: test[[extra],normal]
    assert dep.full_name == "test[[extra],normal]"


# Test serialization with string extras
def test_serialization_with_string_extras():
    """Test serialization when extras is a string"""
    dep = deps.Dependency(name="test", specs=SpecifierSet(), line="test", extras="security")
    
    serialized = dep.serialize()
    # extras should be "security" (the string)
    assert serialized["extras"] == "security"
    
    # Deserialize
    deserialized = deps.Dependency.deserialize(serialized)
    assert deserialized.extras == "security"
    
    # This will have the same issue with full_name
    assert deserialized.full_name == "test[s,e,c,u,r,i,t,y]"


# Test extras as dict (non-iterable for join)
def test_extras_as_dict():
    """Test extras as dictionary - should fail"""
    try:
        dep = deps.Dependency(name="test", specs=SpecifierSet(), line="test", extras={"key": "value"})
        # This should fail when accessing full_name
        full_name = dep.full_name
        # If it somehow works, it would join the keys
        assert full_name == "test[key]"
    except (TypeError, AttributeError):
        pass  # Expected failure


# Test extras as integer
def test_extras_as_integer():
    """Test extras as integer - should fail"""
    dep = deps.Dependency(name="test", specs=SpecifierSet(), line="test", extras=123)
    try:
        full_name = dep.full_name
        assert False, f"Should have failed but got: {full_name}"
    except (TypeError, AttributeError):
        pass  # Expected


# Test with hypothesis - various string inputs as extras
@given(st.text(min_size=1, max_size=20))
def test_extras_string_hypothesis(extras_str):
    """Test various strings as extras value"""
    dep = deps.Dependency(name="package", specs=SpecifierSet(), line="test", extras=extras_str)
    
    # String will be iterated character by character
    full_name = dep.full_name
    expected = f"package[{','.join(extras_str)}]"
    assert full_name == expected