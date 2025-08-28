#!/usr/bin/env python3
"""Test actual plugin loading and error cases"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/lml_env/lib/python3.13/site-packages')

import lml.plugin
from hypothesis import given, strategies as st, assume

# Test: What happens when get_a_plugin is called with non-existent key?
@given(
    plugin_type=st.text(min_size=1, max_size=10),
    existing_key=st.text(min_size=1, max_size=10),
    non_existent_key=st.text(min_size=1, max_size=10)
)
def test_get_plugin_non_existent_key(plugin_type, existing_key, non_existent_key):
    """Test get_a_plugin with non-existent key"""
    assume(existing_key.lower() != non_existent_key.lower())
    
    manager = lml.plugin.PluginManager(plugin_type)
    
    # Register a plugin with existing_key
    @lml.plugin.PluginInfo(plugin_type, tags=[existing_key])
    class TestPlugin:
        pass
    
    manager.register_a_plugin(TestPlugin, 
                             lml.plugin.PluginInfo(plugin_type, tags=[existing_key]))
    
    # Try to get with non-existent key - should raise exception
    try:
        manager.get_a_plugin(non_existent_key)
        assert False, "Should have raised exception"
    except Exception as e:
        assert f"No {plugin_type} is found for {non_existent_key}" in str(e)


# Test: load_me_now with library parameter that doesn't match
@given(
    plugin_type=st.text(min_size=1, max_size=10),
    key=st.text(min_size=1, max_size=10)
)
def test_load_me_now_wrong_library(plugin_type, key):
    """Test load_me_now with wrong library name"""
    manager = lml.plugin.PluginManager(plugin_type)
    
    # Create a test class
    class TestClass:
        __module__ = "actual_module.submodule"
    
    plugin_info = lml.plugin.PluginInfo(
        plugin_type,
        tags=[key]
    )
    plugin_info.cls = TestClass
    
    manager.load_me_later(plugin_info)
    
    # Try to load with wrong library name
    try:
        manager.load_me_now(key, library="wrong-library")
        assert False, "Should have raised exception"
    except Exception as e:
        # Should contain message about library not being installed
        assert "wrong-library is not installed" in str(e) or f"No {plugin_type} is found for {key}" in str(e)


# Test: Empty path splitting
def test_do_import_class_empty_path():
    """Test do_import_class with empty or invalid paths"""
    # Test with no dots - should raise ValueError on rsplit
    try:
        lml.utils.do_import_class("nodots")
        assert False, "Should have raised exception"
    except ValueError:
        pass  # Expected
    except ImportError:
        pass  # Also acceptable if it tries to import


# Test: Registry behavior when plugin_info has no tags
def test_plugin_with_no_explicit_tags():
    """Test plugin registration when tags=None (should use plugin_type as tag)"""
    manager = lml.plugin.PluginManager("test_type")
    
    plugin_info = lml.plugin.PluginInfo(
        "test_type",
        abs_class_path="test.module.Class",
        tags=None  # Explicitly None
    )
    
    manager.load_me_later(plugin_info)
    
    # Should be registered under plugin_type
    assert "test_type" in manager.registry
    assert plugin_info in manager.registry["test_type"]


# Test: Multiple managers for same plugin type
def test_multiple_managers_same_type():
    """Test creating multiple managers for the same plugin type"""
    plugin_type = "shared_type"
    
    # Clear any existing manager
    if plugin_type in lml.plugin.PLUG_IN_MANAGERS:
        del lml.plugin.PLUG_IN_MANAGERS[plugin_type]
    
    manager1 = lml.plugin.PluginManager(plugin_type)
    
    # Creating second manager should replace the first in global registry
    manager2 = lml.plugin.PluginManager(plugin_type)
    
    assert lml.plugin.PLUG_IN_MANAGERS[plugin_type] == manager2
    assert lml.plugin.PLUG_IN_MANAGERS[plugin_type] != manager1


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "-x"])