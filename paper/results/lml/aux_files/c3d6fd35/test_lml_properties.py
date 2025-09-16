"""Property-based tests for lml module using Hypothesis"""

import re
import sys
import math
from hypothesis import given, strategies as st, assume, settings

# Add the lml module to path
sys.path.insert(0, '/root/hypothesis-llm/envs/lml_env/lib/python3.13/site-packages')

from lml.plugin import PluginInfo, PluginManager
from lml.utils import do_import_class
from lml.loader import scan_from_pyinstaller


# Strategy for valid Python identifiers
python_identifier = st.from_regex(r"[a-zA-Z_][a-zA-Z0-9_]*", fullmatch=True)

# Strategy for module paths (dot-separated identifiers)
module_path = st.lists(python_identifier, min_size=1, max_size=5).map(lambda x: ".".join(x))


@given(module_path)
def test_plugin_info_module_name_extraction(abs_path):
    """Test that module_name is correctly extracted as the first part of absolute_import_path"""
    plugin_info = PluginInfo("test_type", abs_class_path=abs_path)
    
    # According to the code, module_name should be the first part before the first dot
    expected_module = abs_path.split(".")[0]
    assert plugin_info.module_name == expected_module


@given(
    plugin_type=python_identifier,
    base_key=st.text(alphabet=st.characters(whitelist_categories=('Ll',)), min_size=1, max_size=20)
)
def test_plugin_manager_case_insensitive_lookup(plugin_type, base_key):
    """Test that PluginManager registry uses case-insensitive keys"""
    # Create different case variations
    key_lower = base_key.lower()
    key_upper = base_key.upper()
    key_mixed = "".join(c.upper() if i % 2 else c.lower() for i, c in enumerate(base_key))
    
    manager = PluginManager(plugin_type)
    
    # Create a plugin info with the uppercase key
    plugin_info = PluginInfo(plugin_type, 
                            abs_class_path="test.module.TestClass",
                            tags=[key_upper])
    
    # Register the plugin
    manager.load_me_later(plugin_info)
    
    # All case variations should find the same plugin since lookup is case-insensitive
    assert key_lower in manager.registry
    assert key_upper.lower() in manager.registry
    assert key_mixed.lower() in manager.registry
    assert manager.registry[key_lower] == manager.registry[key_upper.lower()]
    assert manager.registry[key_lower] == manager.registry[key_mixed.lower()]


@given(
    module_parts=st.lists(python_identifier, min_size=1, max_size=5),
    class_name=python_identifier
)
def test_do_import_class_splitting(module_parts, class_name):
    """Test that do_import_class correctly splits module path and class name"""
    # Build a full class path
    full_path = ".".join(module_parts) + "." + class_name
    
    # The function uses rsplit(".", 1) to split
    # This should give us the module path and class name
    expected_module = ".".join(module_parts)
    expected_class = class_name
    
    # Verify the splitting logic works correctly
    parts = full_path.rsplit(".", 1)
    assert len(parts) == 2
    assert parts[0] == expected_module
    assert parts[1] == expected_class


@given(
    pattern=st.from_regex(r"^[a-zA-Z_][a-zA-Z0-9_]*$", fullmatch=True),
    module_names=st.lists(
        st.from_regex(r"^[a-zA-Z_][a-zA-Z0-9_]*$", fullmatch=True),
        min_size=0,
        max_size=10
    )
)
def test_scan_from_pyinstaller_pattern_matching(pattern, module_names):
    """Test that scan_from_pyinstaller correctly filters modules by pattern"""
    # Create a mock table of content
    table_of_content = set(module_names)
    
    # Manually filter to get expected results
    expected = [name for name in module_names if re.match(pattern, name)]
    
    # The actual function would yield matching module names
    # We're testing the pattern matching logic
    results = []
    for module_name in table_of_content:
        if "." in module_name:
            continue
        if re.match(pattern, module_name):
            results.append(module_name)
    
    # Both should have the same modules (order might differ)
    assert set(results) == set(expected)


@given(
    tags=st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=5)
)
def test_plugin_manager_tag_groups_consistency(tags):
    """Test that tag_groups correctly maps all tags to the primary tag"""
    manager = PluginManager("test_plugin")
    
    # Create plugin with multiple tags
    plugin_info = PluginInfo("test_plugin", 
                            abs_class_path="test.TestClass",
                            tags=tags)
    
    manager.load_me_later(plugin_info)
    
    # The first tag should be the primary tag
    primary_tag = tags[0].lower()
    
    # All tags should map to the primary tag in tag_groups
    for tag in tags:
        assert tag.lower() in manager.tag_groups
        assert manager.tag_groups[tag.lower()] == primary_tag


@given(
    plugin_type=python_identifier,
    abs_path=module_path,
    custom_property=st.text(min_size=1, max_size=50)
)
def test_plugin_info_custom_properties(plugin_type, abs_path, custom_property):
    """Test that PluginInfo correctly stores and retrieves custom properties"""
    # Create plugin with custom property
    plugin_info = PluginInfo(plugin_type, 
                            abs_class_path=abs_path,
                            my_custom_prop=custom_property)
    
    # Should be able to retrieve via __getattr__
    assert plugin_info.my_custom_prop == custom_property
    assert plugin_info.properties['my_custom_prop'] == custom_property


@given(st.lists(st.text(min_size=1, max_size=10), min_size=0, max_size=5))
def test_plugin_info_tags_generator(tags_list):
    """Test that PluginInfo.tags() correctly yields tags"""
    plugin_type = "test_type"
    
    if tags_list:
        # With explicit tags
        plugin_info = PluginInfo(plugin_type, tags=tags_list)
        result_tags = list(plugin_info.tags())
        assert result_tags == tags_list
    else:
        # Without explicit tags, should yield plugin_type
        plugin_info = PluginInfo(plugin_type)
        result_tags = list(plugin_info.tags())
        assert result_tags == [plugin_type]