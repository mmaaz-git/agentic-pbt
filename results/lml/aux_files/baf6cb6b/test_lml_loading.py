#!/usr/bin/env python3
"""Tests for plugin loading and error handling in lml.plugin"""

import sys
import string
from hypothesis import given, strategies as st, assume, settings

# Add the lml_env site-packages to the path  
sys.path.insert(0, '/root/hypothesis-llm/envs/lml_env/lib/python3.13/site-packages')

import lml.plugin
import lml.utils


# Test: Multiple plugins with same key
@given(
    plugin_type=st.text(alphabet=string.ascii_letters, min_size=1, max_size=10),
    shared_key=st.text(alphabet=string.ascii_letters, min_size=1, max_size=10),
    num_plugins=st.integers(min_value=2, max_value=5)
)
def test_multiple_plugins_same_key(plugin_type, shared_key, num_plugins):
    """Test registering multiple plugins with the same key"""
    manager = lml.plugin.PluginManager(plugin_type)
    
    plugins = []
    for i in range(num_plugins):
        plugin_info = lml.plugin.PluginInfo(
            plugin_type,
            abs_class_path=f'test.module.Class{i}',
            tags=[shared_key]
        )
        plugins.append(plugin_info)
        manager.load_me_later(plugin_info)
    
    # All plugins should be in the registry under the shared key
    lower_key = shared_key.lower()
    assert lower_key in manager.registry
    assert len(manager.registry[lower_key]) == num_plugins
    
    # All plugins should be present
    for plugin in plugins:
        assert plugin in manager.registry[lower_key]


# Test: Plugin registration before manager exists (caching)
@given(
    plugin_type=st.text(alphabet=string.ascii_letters, min_size=1, max_size=10),
    tags=st.lists(st.text(alphabet=string.ascii_letters, min_size=1, max_size=10), 
                  min_size=1, max_size=3, unique=True)
)
def test_plugin_caching_before_manager(plugin_type, tags):
    """Test that plugins are cached when registered before manager exists"""
    # Clear any existing managers and cache
    if plugin_type in lml.plugin.PLUG_IN_MANAGERS:
        del lml.plugin.PLUG_IN_MANAGERS[plugin_type]
    if plugin_type in lml.plugin.CACHED_PLUGIN_INFO:
        del lml.plugin.CACHED_PLUGIN_INFO[plugin_type]
    
    # Register plugin before manager exists
    plugin_info = lml.plugin.PluginInfo(
        plugin_type,
        abs_class_path='test.cached.Class',
        tags=tags
    )
    lml.plugin._load_me_later(plugin_info)
    
    # Should be in cache
    assert plugin_type in lml.plugin.CACHED_PLUGIN_INFO
    assert plugin_info in lml.plugin.CACHED_PLUGIN_INFO[plugin_type]
    
    # Create manager - should load cached plugins
    manager = lml.plugin.PluginManager(plugin_type)
    
    # Plugin should now be in manager's registry
    for tag in tags:
        assert tag.lower() in manager.registry
        assert plugin_info in manager.registry[tag.lower()]
    
    # Cache should be cleared
    assert plugin_type not in lml.plugin.CACHED_PLUGIN_INFO


# Test: get_primary_key consistency
@given(
    tags=st.lists(st.text(alphabet=string.ascii_letters, min_size=1, max_size=10),
                  min_size=1, max_size=5, unique=True)
)
def test_get_primary_key_consistency(tags):
    """Test that get_primary_key returns consistent results"""
    manager = lml.plugin.PluginManager("test")
    
    plugin_info = lml.plugin.PluginInfo(
        "test",
        abs_class_path='test.module.Class',
        tags=tags
    )
    
    manager.load_me_later(plugin_info)
    
    # First tag should be primary
    primary = tags[0].lower()
    
    # All tags should return the same primary key
    for tag in tags:
        result = manager.get_primary_key(tag.lower())
        assert result == primary
        
        # Case insensitive
        result_upper = manager.get_primary_key(tag.upper())
        assert result_upper == primary


# Test: PluginInfo as decorator
@given(
    plugin_type=st.text(alphabet=string.ascii_letters, min_size=1, max_size=10),
    tags=st.lists(st.text(alphabet=string.ascii_letters, min_size=1, max_size=10),
                  min_size=1, max_size=3, unique=True)
)
def test_plugin_info_as_decorator(plugin_type, tags):
    """Test PluginInfo used as a class decorator"""
    # Clear any existing managers
    if plugin_type in lml.plugin.PLUG_IN_MANAGERS:
        del lml.plugin.PLUG_IN_MANAGERS[plugin_type]
    
    # Use PluginInfo as decorator
    @lml.plugin.PluginInfo(plugin_type, tags=tags)
    class TestPlugin:
        pass
    
    # Plugin should be registered (in cache or manager)
    if plugin_type in lml.plugin.PLUG_IN_MANAGERS:
        manager = lml.plugin.PLUG_IN_MANAGERS[plugin_type]
        for tag in tags:
            assert tag.lower() in manager.registry
    else:
        # Should be in cache
        assert plugin_type in lml.plugin.CACHED_PLUGIN_INFO
        # Find our plugin in cache
        found = False
        for cached_info in lml.plugin.CACHED_PLUGIN_INFO[plugin_type]:
            if cached_info.cls == TestPlugin:
                found = True
                break
        assert found


# Test: PluginInfoChain add_a_plugin
@given(
    base_path=st.text(alphabet=string.ascii_letters + '.', min_size=1, max_size=30),
    plugin_type=st.text(alphabet=string.ascii_letters, min_size=1, max_size=10),
    submodule=st.text(alphabet=string.ascii_letters, min_size=1, max_size=10)
)
def test_plugin_info_chain_add_plugin(base_path, plugin_type, submodule):
    """Test PluginInfoChain.add_a_plugin method"""
    # Ensure base_path doesn't end with dot
    base_path = base_path.rstrip('.')
    assume(len(base_path) > 0)
    
    # Clear any existing managers and cache
    if plugin_type in lml.plugin.PLUG_IN_MANAGERS:
        del lml.plugin.PLUG_IN_MANAGERS[plugin_type]
    if plugin_type in lml.plugin.CACHED_PLUGIN_INFO:
        del lml.plugin.CACHED_PLUGIN_INFO[plugin_type]
    
    chain = lml.plugin.PluginInfoChain(base_path)
    chain.add_a_plugin(plugin_type, submodule=submodule)
    
    # Should be registered (in cache since no manager exists)
    assert plugin_type in lml.plugin.CACHED_PLUGIN_INFO
    
    # Check the plugin has correct absolute path
    expected_path = f"{base_path}.{submodule}"
    found = False
    for plugin_info in lml.plugin.CACHED_PLUGIN_INFO[plugin_type]:
        if plugin_info.absolute_import_path == expected_path:
            found = True
            break
    assert found


# Test: JSON representation of PluginInfo 
@given(
    plugin_type=st.text(min_size=1, max_size=20),
    path=st.one_of(
        st.none(),
        st.text(min_size=1, max_size=50)
    ),
    properties=st.dictionaries(
        st.text(min_size=1, max_size=10),
        st.one_of(
            st.text(max_size=100),
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.booleans(),
            st.none()
        ),
        max_size=3
    )
)
def test_plugin_info_repr_format(plugin_type, path, properties):
    """Test the __repr__ JSON format of PluginInfo"""
    plugin_info = lml.plugin.PluginInfo(
        plugin_type,
        abs_class_path=path,
        **properties
    )
    
    repr_str = repr(plugin_info)
    
    # Should contain plugin_type
    assert plugin_type in repr_str
    
    # Should contain path if provided
    if path:
        assert path in repr_str
    
    # Should be valid JSON-like format (contains braces)
    assert '{' in repr_str and '}' in repr_str


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])