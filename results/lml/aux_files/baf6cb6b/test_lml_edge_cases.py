#!/usr/bin/env python3
"""Additional edge case property tests for lml.plugin"""

import sys
import string
from hypothesis import given, strategies as st, assume, settings

# Add the lml_env site-packages to the path
sys.path.insert(0, '/root/hypothesis-llm/envs/lml_env/lib/python3.13/site-packages')

import lml.plugin
import lml.utils


# Test edge case: Empty string handling in tags
@given(st.lists(st.text(min_size=0, max_size=10), min_size=1, max_size=5))
def test_plugin_manager_empty_string_tags(tags):
    """Test how PluginManager handles empty strings in tags"""
    manager = lml.plugin.PluginManager("test")
    
    plugin_info = lml.plugin.PluginInfo(
        "test",
        abs_class_path='test.module.TestClass', 
        tags=tags
    )
    
    manager.load_me_later(plugin_info)
    
    # All tags (including empty) should be in registry as lowercase
    for tag in tags:
        assert tag.lower() in manager.registry


# Test: Single component module path
@given(st.text(alphabet=string.ascii_letters + '_', min_size=1, max_size=20))
def test_plugin_info_single_component_path(module_name):
    """Test module name extraction with single component paths"""
    plugin_info = lml.plugin.PluginInfo(
        "test",
        abs_class_path=module_name  # No dots
    )
    
    # Should return the whole string since there's no dot
    assert plugin_info.module_name == module_name


# Test: PluginInfo without absolute_import_path but with cls
@given(
    plugin_type=st.text(min_size=1, max_size=20)
)
def test_plugin_info_cls_module_name(plugin_type):
    """Test module_name when cls is set but not absolute_import_path"""
    plugin_info = lml.plugin.PluginInfo(plugin_type)
    
    # Mock a class with __module__
    class TestClass:
        __module__ = "test.module"
    
    plugin_info.cls = TestClass
    
    # Should get module name from cls.__module__
    assert plugin_info.module_name == "test.module"


# Test: Very long module paths
@given(
    st.integers(min_value=10, max_value=50).flatmap(
        lambda n: st.lists(
            st.text(alphabet=string.ascii_letters, min_size=1, max_size=10),
            min_size=n, max_size=n
        )
    )
)
def test_long_module_paths(components):
    """Test with very long module paths"""
    path = '.'.join(components)
    
    plugin_info = lml.plugin.PluginInfo(
        "test",
        abs_class_path=path
    )
    
    # Should still extract first component
    assert plugin_info.module_name == components[0]


# Test: Unicode in custom properties  
@given(
    properties=st.dictionaries(
        st.text(min_size=1, max_size=10),
        st.text(min_size=0, max_size=100),
        max_size=5
    )
)
def test_plugin_info_unicode_properties(properties):
    """Test that PluginInfo handles Unicode in custom properties"""
    plugin_info = lml.plugin.PluginInfo(
        "test",
        abs_class_path="test.module.Class",
        **properties
    )
    
    # Should be able to access all properties via __getattr__
    for key, value in properties.items():
        assert plugin_info.__getattr__(key) == value


# Test: Registry behavior with duplicate tags
@given(
    st.lists(st.text(alphabet=string.ascii_lowercase, min_size=1, max_size=5), 
             min_size=2, max_size=10)
)
def test_duplicate_tags_in_list(tags):
    """Test how duplicate tags in the same plugin are handled"""
    manager = lml.plugin.PluginManager("test")
    
    plugin_info = lml.plugin.PluginInfo(
        "test",
        abs_class_path="test.module.Class",
        tags=tags  # May contain duplicates
    )
    
    manager.load_me_later(plugin_info)
    
    # Even with duplicates, plugin should be registered
    for tag in set(tags):  # Use set to get unique tags
        assert tag.lower() in manager.registry
        assert plugin_info in manager.registry[tag.lower()]


# Test: Case preservation in original tags vs registry keys
@given(
    tags=st.lists(
        st.text(alphabet=string.ascii_letters, min_size=1, max_size=10),
        min_size=1, max_size=5, unique=True
    )
)
def test_case_preservation_in_tags(tags):
    """Test that original case is preserved in tags() but registry uses lowercase"""
    plugin_info = lml.plugin.PluginInfo(
        "test",
        abs_class_path="test.module.Class",
        tags=tags
    )
    
    # Original case should be preserved in tags()
    assert list(plugin_info.tags()) == tags
    
    # But registry should use lowercase
    manager = lml.plugin.PluginManager("test")
    manager.load_me_later(plugin_info)
    
    for tag in tags:
        # Registry uses lowercase
        assert tag.lower() in manager.registry
        # Original case tags might not be in registry
        if tag != tag.lower():
            assert tag not in manager.registry or tag.lower() == tag


# Test: Special characters in module paths
@given(st.text(alphabet=string.printable, min_size=1, max_size=50))
def test_module_path_with_special_chars(path):
    """Test that special characters in paths are handled"""
    # This might expose issues if the path contains dots or other special chars
    plugin_info = lml.plugin.PluginInfo(
        "test",
        abs_class_path=path
    )
    
    # module_name extraction should handle this gracefully
    if '.' in path:
        expected = path.split('.')[0]
    else:
        expected = path
    
    assert plugin_info.module_name == expected


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])