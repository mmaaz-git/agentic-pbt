#!/usr/bin/env python3
"""Property-based tests for lml.plugin module using Hypothesis"""

import sys
import string
from hypothesis import given, strategies as st, assume, settings
from hypothesis.strategies import composite

# Add the lml_env site-packages to the path
sys.path.insert(0, '/root/hypothesis-llm/envs/lml_env/lib/python3.13/site-packages')

import lml.plugin
import lml.utils


# Strategy for generating valid Python identifiers
@composite
def python_identifier(draw):
    """Generate a valid Python identifier"""
    first_char = draw(st.sampled_from(string.ascii_letters + '_'))
    rest = draw(st.text(alphabet=string.ascii_letters + string.digits + '_', min_size=0, max_size=20))
    return first_char + rest


# Strategy for generating module paths
@composite
def module_path(draw):
    """Generate a valid module path like 'package.submodule.Class'"""
    num_parts = draw(st.integers(min_value=2, max_value=5))
    parts = [draw(python_identifier()) for _ in range(num_parts)]
    return '.'.join(parts)


# Test 1: Case insensitivity in PluginManager
@given(
    plugin_type=python_identifier(),
    key=st.text(alphabet=string.ascii_letters + string.digits, min_size=1, max_size=20)
)
def test_plugin_manager_case_insensitive_registry(plugin_type, key):
    """Test that PluginManager treats keys case-insensitively"""
    manager = lml.plugin.PluginManager(plugin_type)
    
    # Create a plugin info with the key
    plugin_info = lml.plugin.PluginInfo(
        plugin_type, 
        abs_class_path='test.module.TestClass',
        tags=[key]
    )
    
    # Register it
    manager.load_me_later(plugin_info)
    
    # Should be retrievable with any case variation
    lower_key = key.lower()
    upper_key = key.upper()
    
    # Check registry contains the lowercase version
    assert lower_key in manager.registry
    
    # Check that different case variations map to same primary tag
    if lower_key in manager.tag_groups:
        assert manager.get_primary_key(lower_key) == manager.get_primary_key(upper_key)


# Test 2: Module name extraction property
@given(module_path())
def test_plugin_info_module_name_extraction(path):
    """Test that module_name is correctly extracted as first part of absolute_import_path"""
    plugin_info = lml.plugin.PluginInfo(
        "test_type",
        abs_class_path=path
    )
    
    # The module_name should be the first part before the first dot
    expected_module = path.split('.')[0]
    assert plugin_info.module_name == expected_module


# Test 3: Path construction in PluginInfoChain
@given(
    base_path=module_path(),
    submodule=python_identifier()
)
def test_plugin_info_chain_path_construction(base_path, submodule):
    """Test that PluginInfoChain correctly constructs absolute paths"""
    chain = lml.plugin.PluginInfoChain(base_path)
    
    # The _get_abs_path should concatenate with a dot
    result = chain._get_abs_path(submodule)
    expected = f"{base_path}.{submodule}"
    assert result == expected


# Test 4: Tag group consistency - first tag becomes primary
@given(
    plugin_type=python_identifier(),
    tags=st.lists(python_identifier(), min_size=1, max_size=5, unique=True)
)
def test_plugin_manager_primary_tag_consistency(plugin_type, tags):
    """Test that the first tag becomes the primary tag for all tags"""
    manager = lml.plugin.PluginManager(plugin_type)
    
    plugin_info = lml.plugin.PluginInfo(
        plugin_type,
        abs_class_path='test.module.TestClass',
        tags=tags
    )
    
    manager.load_me_later(plugin_info)
    
    # The first tag (lowercased) should be the primary tag
    primary_tag = tags[0].lower()
    
    # All tags should map to the same primary tag
    for tag in tags:
        assert manager.get_primary_key(tag.lower()) == primary_tag


# Test 5: Import path splitting for class imports
@given(module_path())
def test_do_import_class_path_splitting(path):
    """Test that import paths are split correctly on the last dot"""
    assume('.' in path)  # We need at least one dot for this to work
    
    # The rsplit behavior used in do_import_class (line 54)
    module_name, class_name = path.rsplit('.', 1)
    
    # Verify the split preserves the original when joined
    assert f"{module_name}.{class_name}" == path
    
    # Verify no dots in class_name (it should be the last part)
    assert '.' not in class_name
    
    # Verify module_name + class_name reconstruct the original
    reconstructed = '.'.join([module_name, class_name])
    assert reconstructed == path


# Test 6: Registry round-trip property
@given(
    plugin_type=python_identifier(),
    tags=st.lists(python_identifier(), min_size=1, max_size=3, unique=True)
)
def test_plugin_manager_registry_round_trip(plugin_type, tags):
    """Test that plugins registered can be found by all their tags"""
    manager = lml.plugin.PluginManager(plugin_type)
    
    # Create and register a plugin
    test_class_path = 'test.module.TestClass'
    plugin_info = lml.plugin.PluginInfo(
        plugin_type,
        abs_class_path=test_class_path,
        tags=tags
    )
    
    manager.load_me_later(plugin_info)
    
    # Verify it's in the registry under all tags
    for tag in tags:
        lower_tag = tag.lower()
        assert lower_tag in manager.registry
        assert plugin_info in manager.registry[lower_tag]


# Test 7: PluginInfo tags() generator behavior
@given(
    plugin_type=python_identifier(),
    custom_tags=st.one_of(
        st.none(),
        st.lists(python_identifier(), min_size=1, max_size=5)
    )
)
def test_plugin_info_tags_generator(plugin_type, custom_tags):
    """Test that tags() yields the right sequence based on __tags"""
    plugin_info = lml.plugin.PluginInfo(
        plugin_type,
        abs_class_path='test.module.TestClass',
        tags=custom_tags
    )
    
    result_tags = list(plugin_info.tags())
    
    if custom_tags is None:
        # Should yield just the plugin_type
        assert result_tags == [plugin_type]
    else:
        # Should yield the custom tags
        assert result_tags == custom_tags


# Test 8: JSON serialization doesn't crash
@given(
    plugin_type=python_identifier(),
    path=module_path(),
    properties=st.dictionaries(
        python_identifier(),
        st.one_of(st.text(), st.integers(), st.floats(allow_nan=False), st.booleans()),
        max_size=5
    )
)
def test_plugin_info_json_representation(plugin_type, path, properties):
    """Test that PluginInfo can be serialized to JSON without crashing"""
    plugin_info = lml.plugin.PluginInfo(
        plugin_type,
        abs_class_path=path,
        **properties
    )
    
    # Should not crash when converting to string (uses json_dumps internally)
    result = str(plugin_info)
    assert isinstance(result, str)
    assert plugin_type in result
    assert path in result


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])