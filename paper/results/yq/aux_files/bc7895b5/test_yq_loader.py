import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/yq_env/lib/python3.13/site-packages')

import yaml
import yq.loader
from hypothesis import given, assume, strategies as st, settings
import pytest

# Property 1: set_yaml_grammar should only accept valid grammar versions
@given(st.text())
def test_set_yaml_grammar_validates_version(version):
    """set_yaml_grammar raises exception for unknown grammar versions (line 115-116)"""
    resolver = yaml.SafeLoader
    if version not in ["1.1", "1.2"]:
        with pytest.raises(Exception) as excinfo:
            yq.loader.set_yaml_grammar(resolver, version)
        assert f"Unknown grammar version {version}" in str(excinfo.value)
    else:
        # Should not raise for valid versions
        yq.loader.set_yaml_grammar(resolver, version)

# Property 2: hash_key is deterministic
@given(st.one_of(st.text(), st.binary()))
def test_hash_key_deterministic(key):
    """hash_key should always return same output for same input"""
    result1 = yq.loader.hash_key(key)
    result2 = yq.loader.hash_key(key)
    assert result1 == result2
    assert isinstance(result1, str)

# Property 3: hash_key handles both strings and bytes equivalently when content is same
@given(st.text().filter(lambda x: x.isascii()))
def test_hash_key_string_bytes_equivalence(text):
    """hash_key should produce same hash for equivalent string and bytes"""
    str_hash = yq.loader.hash_key(text)
    bytes_hash = yq.loader.hash_key(text.encode())
    assert str_hash == bytes_hash

# Property 4: get_loader returns a valid loader class
@given(
    st.booleans(),  # use_annotations
    st.booleans(),  # expand_aliases  
    st.booleans()   # expand_merge_keys
)
def test_get_loader_returns_valid_class(use_annotations, expand_aliases, expand_merge_keys):
    """get_loader should always return a YAML loader class"""
    loader_class = yq.loader.get_loader(
        use_annotations=use_annotations,
        expand_aliases=expand_aliases,
        expand_merge_keys=expand_merge_keys
    )
    # Should be a class, not an instance
    assert isinstance(loader_class, type)
    # Should be a subclass of yaml.SafeLoader or CustomLoader
    assert issubclass(loader_class, (yaml.SafeLoader, yq.loader.CustomLoader))

# Property 5: set_yaml_grammar properly configures resolver
@given(st.sampled_from(["1.1", "1.2"]), st.booleans())
def test_set_yaml_grammar_configures_resolver(version, expand_merge_keys):
    """set_yaml_grammar should properly configure yaml_implicit_resolvers"""
    class TestResolver:
        yaml_implicit_resolvers = {}
    
    resolver = TestResolver()
    yq.loader.set_yaml_grammar(resolver, version, expand_merge_keys)
    
    # Should have implicit resolvers set
    assert hasattr(resolver, 'yaml_implicit_resolvers')
    assert isinstance(resolver.yaml_implicit_resolvers, dict)
    
    # Based on core_resolvers in the code
    if version == "1.1":
        # Version 1.1 has specific start chars for booleans
        assert any('y' in chars for chars in resolver.yaml_implicit_resolvers.keys())
        assert any('n' in chars for chars in resolver.yaml_implicit_resolvers.keys())
    
    if expand_merge_keys:
        # Should have merge resolver if expand_merge_keys is True
        assert '<' in resolver.yaml_implicit_resolvers

# Property 6: CustomLoader expand_aliases attribute
def test_custom_loader_has_expand_aliases():
    """CustomLoader should have expand_aliases attribute set to False"""
    assert hasattr(yq.loader.CustomLoader, 'expand_aliases')
    assert yq.loader.CustomLoader.expand_aliases == False

# Property 7: get_loader with expand_aliases affects loader class
def test_get_loader_expand_aliases_affects_class():
    """get_loader should return CustomLoader when expand_aliases=False"""
    loader_with_expand = yq.loader.get_loader(expand_aliases=True)
    loader_without_expand = yq.loader.get_loader(expand_aliases=False)
    
    # When expand_aliases=False, should use CustomLoader
    assert loader_without_expand == yq.loader.CustomLoader

# Property 8: hash_key output format invariant
@given(st.one_of(st.text(), st.binary()))
def test_hash_key_output_format(key):
    """hash_key should always return base64-encoded string"""
    result = yq.loader.hash_key(key)
    assert isinstance(result, str)
    # Base64 strings should only contain these characters
    import string
    base64_chars = string.ascii_letters + string.digits + '+/='
    assert all(c in base64_chars for c in result)

# Property 9: set_yaml_grammar idempotence
@given(st.sampled_from(["1.1", "1.2"]), st.booleans())
def test_set_yaml_grammar_idempotent(version, expand_merge_keys):
    """Calling set_yaml_grammar twice with same params should have same effect"""
    class TestResolver1:
        yaml_implicit_resolvers = {}
    class TestResolver2:
        yaml_implicit_resolvers = {}
    
    yq.loader.set_yaml_grammar(TestResolver1, version, expand_merge_keys)
    yq.loader.set_yaml_grammar(TestResolver2, version, expand_merge_keys)
    yq.loader.set_yaml_grammar(TestResolver2, version, expand_merge_keys)  # Second call
    
    # Both resolvers should have identical configuration
    assert TestResolver1.yaml_implicit_resolvers == TestResolver2.yaml_implicit_resolvers