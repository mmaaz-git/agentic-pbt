"""
Focused test demonstrating the Config.get_namespace bug
"""

from hypothesis import given, strategies as st
from flask import Config
import string


@given(
    # Generate keys that differ only in case
    base_key=st.text(min_size=1, max_size=10, alphabet=string.ascii_letters),
    prefix=st.text(min_size=1, max_size=5, alphabet=string.ascii_uppercase),
    values=st.lists(st.text(), min_size=2, max_size=5)
)
def test_config_namespace_key_collision_bug(base_key, prefix, values):
    """
    Bug: Config.get_namespace with lowercase=True (default) causes key collisions
    when config keys differ only in case.
    """
    if len(values) < 2:
        return  # Need at least 2 values
    
    config = Config('.')
    
    # Create keys that differ only in case
    key1 = f"{prefix}_{base_key.upper()}"
    key2 = f"{prefix}_{base_key.lower()}"
    
    if key1 == key2:  # Skip if they're the same
        return
    
    # Set different values
    config[key1] = values[0]
    config[key2] = values[1]
    
    # Both keys should exist in config
    assert key1 in config
    assert key2 in config
    assert config[key1] == values[0]
    assert config[key2] == values[1]
    
    # Get namespace with default lowercase=True
    namespace = config.get_namespace(f"{prefix}_")
    
    # BUG: Only one key appears in namespace due to case collision
    # Both values are lost except the last one
    expected_keys = 2  # We added 2 different keys
    actual_keys = len(namespace)
    
    # This assertion will fail, demonstrating the bug
    assert actual_keys == expected_keys, \
        f"Expected {expected_keys} keys in namespace, but got {actual_keys}. " \
        f"Keys {key1} and {key2} collided to single key '{base_key.lower()}'"


# Minimal reproduction
def test_config_namespace_minimal_repro():
    """Minimal test case showing the bug"""
    config = Config('.')
    
    # Set config values with same prefix but different case
    config['API_KeyName'] = 'value1'  
    config['API_KEYNAME'] = 'value2'
    config['API_keyname'] = 'value3'
    
    # Get namespace
    namespace = config.get_namespace('API_')
    
    # BUG: All three keys collapse to one 'keyname' key
    # Only the last value survives
    print(f"Config has {len([k for k in config if k.startswith('API_')])} keys")
    print(f"Namespace has {len(namespace)} keys") 
    print(f"Namespace: {dict(namespace)}")
    
    # This fails - we lose data due to key collision
    assert len(namespace) == 3, "Three different config keys should result in three namespace entries"


if __name__ == "__main__":
    # Run the minimal repro to show the bug
    test_config_namespace_minimal_repro()