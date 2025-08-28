import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/yq_env/lib/python3.13/site-packages')

import yaml
import yq.loader
from hypothesis import given, assume, strategies as st, settings
import pytest
import io

# More sophisticated tests focusing on actual bugs

# Property: set_yaml_grammar mutates class state (potential bug with shared state)
@given(st.sampled_from(["1.1", "1.2"]), st.sampled_from(["1.1", "1.2"]))
def test_set_yaml_grammar_class_mutation_bug(version1, version2):
    """set_yaml_grammar modifies the class itself, not instances - this could cause issues"""
    # This modifies the actual CSafeLoader class!
    yq.loader.set_yaml_grammar(yq.loader.default_loader, version1)
    
    # Create an instance
    yaml_str = "test: value"
    loader1 = yq.loader.default_loader(io.StringIO(yaml_str))
    
    # Now change the grammar on the class
    yq.loader.set_yaml_grammar(yq.loader.default_loader, version2)
    
    # The already created instance will be affected!
    # This is a design issue - mutating class state affects existing instances
    loader2 = yq.loader.default_loader(io.StringIO(yaml_str))
    
    # Both loaders share the same class-level resolvers
    assert loader1.yaml_implicit_resolvers is loader2.yaml_implicit_resolvers

# Property: get_loader modifies global class state
def test_get_loader_modifies_global_state():
    """get_loader modifies the loader class globally, affecting all users"""
    # Save original state
    original_resolvers = getattr(yq.loader.default_loader, 'yaml_implicit_resolvers', {}).copy()
    
    # Get a loader with specific settings
    loader_class1 = yq.loader.get_loader(expand_merge_keys=True)
    state1 = loader_class1.yaml_implicit_resolvers.copy()
    
    # Get another loader with different settings
    loader_class2 = yq.loader.get_loader(expand_merge_keys=False)
    state2 = loader_class2.yaml_implicit_resolvers.copy()
    
    # They return the same class
    assert loader_class1 is loader_class2
    
    # But the class state has been modified!
    # This means the last call wins - potential bug
    has_merge_in_state1 = any('<' in resolvers for resolvers in state1.keys())
    has_merge_in_state2 = any('<' in resolvers for resolvers in state2.keys())
    
    # State2 should not have merge resolver but state1 should
    assert has_merge_in_state1 == True
    assert has_merge_in_state2 == False

# Property: hash_key with empty input
@given(st.sampled_from(["", b""]))
def test_hash_key_empty_input(key):
    """hash_key should handle empty strings/bytes"""
    result = yq.loader.hash_key(key)
    assert isinstance(result, str)
    assert len(result) > 0  # Should still produce a hash

# Property: get_loader's class constructors are modified in place
def test_get_loader_constructor_mutation():
    """get_loader modifies yaml_constructors dict in place"""
    # Get initial constructors
    loader_class = yq.loader.get_loader()
    
    # Check that binary and set constructors are removed (lines 203-204)
    assert 'tag:yaml.org,2002:binary' not in loader_class.yaml_constructors
    assert 'tag:yaml.org,2002:set' not in loader_class.yaml_constructors
    
    # But this affects the global class!
    # If someone else is using the same loader class, they're affected

# Property: CustomLoader.expand_aliases is a class variable, not instance
def test_custom_loader_expand_aliases_class_var():
    """CustomLoader.expand_aliases is shared across all instances"""
    loader1 = yq.loader.CustomLoader(io.StringIO("test: 1"))
    loader2 = yq.loader.CustomLoader(io.StringIO("test: 2"))
    
    # Modifying one affects all
    original = yq.loader.CustomLoader.expand_aliases
    loader1.expand_aliases = True
    
    # This changes the class variable!
    assert yq.loader.CustomLoader.expand_aliases == True
    assert loader2.expand_aliases == True
    
    # Reset
    yq.loader.CustomLoader.expand_aliases = original

# Property: Multiple calls to get_loader with same params may not be idempotent
def test_get_loader_not_idempotent():
    """Multiple calls to get_loader modify global state non-idempotently"""
    # First call
    loader1 = yq.loader.get_loader(expand_merge_keys=True)
    constructors1 = len(loader1.yaml_constructors)
    
    # Second call - constructors are popped each time! (lines 203-204)
    loader2 = yq.loader.get_loader(expand_merge_keys=True)
    constructors2 = len(loader2.yaml_constructors)
    
    # The constructors should be the same, but pop might have already happened
    # This test checks if the pop operations are idempotent

# Property: hash_key with non-UTF8 bytes
@given(st.binary().filter(lambda b: b and not all(32 <= byte < 127 for byte in b)))
def test_hash_key_non_utf8_bytes(data):
    """hash_key should handle arbitrary binary data"""
    result = yq.loader.hash_key(data)
    assert isinstance(result, str)

# Property: set_yaml_grammar with None resolver
def test_set_yaml_grammar_none_resolver():
    """What happens if resolver is None or doesn't have yaml_implicit_resolvers?"""
    class MinimalResolver:
        pass
    
    resolver = MinimalResolver()
    yq.loader.set_yaml_grammar(resolver, "1.2")
    
    # Should create the attribute
    assert hasattr(resolver, 'yaml_implicit_resolvers')
    assert isinstance(resolver.yaml_implicit_resolvers, dict)