#!/usr/bin/env python3
"""Looking for edge case bugs in lml.plugin"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/lml_env/lib/python3.13/site-packages')

import lml.plugin
import lml.utils
from hypothesis import given, strategies as st


# Test: What happens with empty string plugin type?
def test_empty_plugin_type():
    """Test plugin with empty string as type"""
    # This might cause issues in lookups
    manager = lml.plugin.PluginManager("")
    
    plugin_info = lml.plugin.PluginInfo(
        "",
        abs_class_path="test.module.Class",
        tags=["tag1"]
    )
    
    manager.load_me_later(plugin_info)
    assert "tag1" in manager.registry
    

# Test: Module name with trailing dots
@given(st.text(alphabet="abcdefghijk.", min_size=1, max_size=20))
def test_module_name_with_dots(path):
    """Test module name extraction with various dot patterns"""
    plugin_info = lml.plugin.PluginInfo(
        "test",
        abs_class_path=path
    )
    
    # Should not crash
    module_name = plugin_info.module_name
    
    # Verify behavior with edge cases
    if '.' in path:
        # Should be first part before first dot
        assert module_name == path.split('.')[0]
    else:
        # No dots means whole string
        assert module_name == path


# Test: PluginInfo with both cls and absolute_import_path
def test_plugin_info_cls_and_path():
    """Test when both cls and absolute_import_path are set"""
    class TestClass:
        __module__ = "from_cls_module"
    
    plugin_info = lml.plugin.PluginInfo(
        "test",
        abs_class_path="from_path.module.Class"
    )
    plugin_info.cls = TestClass
    
    # According to code, absolute_import_path takes precedence
    assert plugin_info.module_name == "from_path"  # Not "from_cls_module"


# Test: Empty tags list
def test_empty_tags_list():
    """Test plugin with empty tags list"""
    plugin_info = lml.plugin.PluginInfo(
        "test_type",
        abs_class_path="test.module.Class",
        tags=[]  # Empty list
    )
    
    manager = lml.plugin.PluginManager("test_type")
    manager.load_me_later(plugin_info)
    
    # With empty tags list, nothing should be registered
    # This might be unexpected behavior!
    assert len(manager.registry) == 0


# Test: Unicode in plugin types and tags
@given(
    plugin_type=st.text(min_size=1, max_size=10),
    tags=st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=3)
)
def test_unicode_everywhere(plugin_type, tags):
    """Test Unicode strings in all plugin fields"""
    manager = lml.plugin.PluginManager(plugin_type)
    
    plugin_info = lml.plugin.PluginInfo(
        plugin_type,
        abs_class_path="test.module.Class",
        tags=tags
    )
    
    manager.load_me_later(plugin_info)
    
    # Should handle Unicode properly
    for tag in tags:
        assert tag.lower() in manager.registry


# Test: What happens with None in tags list?
def test_none_in_tags():
    """Test what happens if None appears in tags list"""
    manager = lml.plugin.PluginManager("test")
    
    # This might cause AttributeError on .lower()
    try:
        plugin_info = lml.plugin.PluginInfo(
            "test",
            abs_class_path="test.module.Class",
            tags=["valid", None, "another"]  # None in the middle
        )
        manager.load_me_later(plugin_info)
        # If we get here, check what happened
        print(f"Registry keys: {list(manager.registry.keys())}")
    except AttributeError as e:
        # This would be a bug - None should be handled gracefully
        print(f"Bug found: {e}")
        return True
    
    return False


# Test: Registry pollution across tests
def test_registry_isolation():
    """Test that plugin managers are properly isolated"""
    # Create two different plugin types
    manager1 = lml.plugin.PluginManager("type1") 
    manager2 = lml.plugin.PluginManager("type2")
    
    plugin1 = lml.plugin.PluginInfo("type1", abs_class_path="test1.Class", tags=["tag1"])
    plugin2 = lml.plugin.PluginInfo("type2", abs_class_path="test2.Class", tags=["tag2"])
    
    manager1.load_me_later(plugin1)
    manager2.load_me_later(plugin2)
    
    # Each manager should only have its own plugins
    assert "tag1" in manager1.registry
    assert "tag2" not in manager1.registry
    assert "tag2" in manager2.registry
    assert "tag1" not in manager2.registry


# Test: get_a_plugin actually instantiates the class
def test_get_a_plugin_instantiation():
    """Test that get_a_plugin creates an instance"""
    manager = lml.plugin.PluginManager("test")
    
    class TestPlugin:
        def __init__(self):
            self.initialized = True
    
    plugin_info = lml.plugin.PluginInfo("test", tags=["test_tag"])
    plugin_info.cls = TestPlugin
    
    manager.load_me_later(plugin_info)
    
    # get_a_plugin should return an instance
    instance = manager.get_a_plugin("test_tag")
    assert isinstance(instance, TestPlugin)
    assert instance.initialized == True


if __name__ == "__main__":
    # Run tests
    print("Testing empty plugin type...")
    test_empty_plugin_type()
    print("✓ Passed\n")
    
    print("Testing plugin info with cls and path...")
    test_plugin_info_cls_and_path()
    print("✓ Passed\n")
    
    print("Testing empty tags list...")
    test_empty_tags_list()
    print("✓ Passed - but this might be unexpected behavior!\n")
    
    print("Testing None in tags...")
    if test_none_in_tags():
        print("✗ Bug found: None in tags causes AttributeError\n")
    else:
        print("✓ Passed\n")
    
    print("Testing registry isolation...")
    test_registry_isolation()
    print("✓ Passed\n")
    
    print("Testing get_a_plugin instantiation...")
    test_get_a_plugin_instantiation()
    print("✓ Passed\n")
    
    # Run hypothesis tests
    import pytest
    pytest.main([__file__, "-v", "-k", "test_module_name_with_dots or test_unicode_everywhere"])