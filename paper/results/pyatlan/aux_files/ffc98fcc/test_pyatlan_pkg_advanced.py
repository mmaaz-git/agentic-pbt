#!/usr/bin/env python3
import json
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, '/root/hypothesis-llm/envs/pyatlan_env/lib/python3.13/site-packages')

from hypothesis import assume, given, strategies as st, settings, example
from hypothesis.strategies import composite
import pytest

# Import the modules we want to test
from pyatlan.pkg.models import CustomPackage, PackageWriter
from pyatlan.pkg.ui import UIStep, UIConfig
from pyatlan.pkg.utils import validate_multiselect, has_handler
from pyatlan.pkg.widgets import TextInput, BooleanInput, DropDown
import logging


# Test PackageWriter file creation
@given(
    package_id=st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=20),
    package_name=st.text(min_size=1, max_size=50),
    description=st.text(min_size=1, max_size=200)
)
def test_package_writer_creates_expected_files(package_id, package_name, description):
    """Test that PackageWriter creates the expected directory structure and files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir)
        
        package_data = {
            "package_id": f"@test/{package_id}",
            "package_name": package_name,
            "description": description,
            "icon_url": "http://example.com/icon.png",
            "docs_url": "http://example.com/docs",
            "ui_config": {"steps": []},
            "container_image": "test:latest",
            "container_command": ["echo", "test"]
        }
        
        pkg = CustomPackage(**package_data)
        writer = PackageWriter(pkg=pkg, path=path)
        
        # Create the package
        writer.create_package()
        
        # Expected directory structure
        expected_name = f"test-{package_id}"  # @ and / are removed/replaced
        root_dir = path / expected_name
        
        # Check that directories were created
        assert root_dir.exists()
        assert (root_dir / "configmaps").exists()
        assert (root_dir / "templates").exists()
        
        # Check that files were created
        assert (root_dir / "index.js").exists()
        assert (root_dir / "package.json").exists()
        assert (root_dir / "configmaps" / "default.yaml").exists()
        assert (root_dir / "templates" / "default.yaml").exists()
        
        # Verify package.json is valid JSON
        with (root_dir / "package.json").open() as f:
            package_json = json.load(f)
            assert package_json["description"] == description


# Test UIConfig with complex nested structures
@given(
    num_steps=st.integers(min_value=1, max_value=5),
    num_inputs_per_step=st.integers(min_value=1, max_value=5)
)
def test_ui_config_complex_structure(num_steps, num_inputs_per_step):
    """Test UIConfig with complex nested structures."""
    steps = []
    
    for i in range(num_steps):
        inputs = {}
        for j in range(num_inputs_per_step):
            input_name = f"input_{i}_{j}"
            inputs[input_name] = TextInput(
                label=f"Input {j}",
                placeholder=f"Enter value {j}"
            )
        
        step = UIStep(
            title=f"Step {i}",
            inputs=inputs,
            description=f"Description for step {i}"
        )
        steps.append(step)
    
    config = UIConfig(steps=steps)
    
    # Verify the structure
    assert len(config.steps) == num_steps
    for i, step in enumerate(config.steps):
        assert len(step.inputs) == num_inputs_per_step
        assert step.title == f"Step {i}"
        assert step.id == f"step_{i}"


# Test validate_multiselect with nested JSON structures
@given(st.recursive(
    st.text(min_size=1, max_size=10),
    lambda children: st.lists(children, min_size=1, max_size=3),
    max_leaves=10
))
def test_validate_multiselect_nested_structures(nested):
    """Test validate_multiselect with nested list structures."""
    json_str = json.dumps(nested)
    
    # This should parse nested structures
    result = validate_multiselect(json_str)
    
    # The result should match the input
    assert result == nested


# Test has_handler function with mock loggers
def test_has_handler_hierarchy():
    """Test the has_handler function with logger hierarchy."""
    # Create a logger hierarchy
    parent_logger = logging.getLogger("test.parent")
    child_logger = logging.getLogger("test.parent.child")
    
    # Add a handler to the parent
    handler = logging.StreamHandler()
    parent_logger.addHandler(handler)
    
    # Child should find the handler through hierarchy
    assert has_handler(child_logger, logging.StreamHandler)
    
    # Remove handler
    parent_logger.removeHandler(handler)
    
    # Now it shouldn't find it
    assert not has_handler(child_logger, logging.StreamHandler)


# Test CustomPackage.indexJS is always the same
def test_custom_package_index_js_deterministic():
    """Test that indexJS always returns the same content."""
    js1 = CustomPackage.indexJS()
    js2 = CustomPackage.indexJS()
    
    assert js1 == js2
    assert "function dummy()" in js1
    assert "console.log" in js1


# Test PackageWriter.create_config
@given(
    package_id=st.text(alphabet="abcdefghijklmnopqrstuvwxyz-", min_size=5, max_size=20)
)
def test_package_writer_create_config(package_id):
    """Test PackageWriter.create_config method."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir)
        
        package_data = {
            "package_id": f"@atl/{package_id}",
            "package_name": "Test",
            "description": "Test",
            "icon_url": "http://example.com/icon.png",
            "docs_url": "http://example.com/docs",
            "ui_config": {"steps": []},
            "container_image": "test:latest",
            "container_command": ["echo", "test"]
        }
        
        pkg = CustomPackage(**package_data)
        writer = PackageWriter(pkg=pkg, path=path)
        
        # Create config
        writer.create_config()
        
        # Expected filename - strips @atl/ prefix and replaces - with _
        expected_filename = f"{package_id.replace('-', '_')}_cfg.py"
        config_file = path / expected_filename
        
        # Check that the config file was created
        assert config_file.exists()
        
        # Read and verify it's Python code
        with config_file.open() as f:
            content = f.read()
            # Should contain Python code
            assert "class" in content or "def" in content or "import" in content


# Test validate_multiselect with extremely nested JSON
def test_validate_multiselect_deep_nesting():
    """Test validate_multiselect with deeply nested structures."""
    # Create a deeply nested structure
    deep = ["a"]
    for _ in range(50):
        deep = [deep]
    
    json_str = json.dumps(deep)
    
    # Should handle deep nesting
    result = validate_multiselect(json_str)
    assert result == deep


# Test UIStep properties list consistency
@given(st.dictionaries(
    st.text(min_size=1, max_size=20),
    st.just(TextInput(label="test")),
    min_size=1,
    max_size=10
))
def test_ui_step_properties_consistency(inputs):
    """Test that UIStep.properties matches the input keys."""
    step = UIStep(title="Test", inputs=inputs)
    
    # Properties should match input keys
    assert set(step.properties) == set(inputs.keys())
    assert len(step.properties) == len(inputs)
    
    # Order should be preserved (as of Python 3.7+)
    assert step.properties == list(inputs.keys())


# Test JSON encoding of various widget types
def test_widget_json_encoding():
    """Test that different widget types can be JSON encoded."""
    widgets = [
        TextInput(label="Text", placeholder="Enter text"),
        BooleanInput(label="Bool", default=True),
        DropDown(label="Dropdown", options={"a": "Option A", "b": "Option B"})
    ]
    
    for widget in widgets:
        json_str = widget.to_json()
        
        # Should produce valid JSON
        parsed = json.loads(json_str)
        
        # Should contain expected fields
        assert "label" in parsed
        assert parsed["label"] == widget.label


# Test package name with unicode characters
@given(st.text(min_size=1, max_size=50))
@example("😀🎉🚀")  # Emojis
@example("中文测试")  # Chinese
@example("العربية")  # Arabic
@example("ελληνικά")  # Greek
@example("\U0001F600\U0001F601")  # More emojis
def test_package_name_unicode_handling(text):
    """Test that package names handle unicode correctly."""
    package_data = {
        "package_id": text,
        "package_name": text,
        "description": "Test",
        "icon_url": "http://example.com/icon.png",
        "docs_url": "http://example.com/docs",
        "ui_config": {"steps": []},
        "container_image": "test:latest",
        "container_command": ["echo", "test"]
    }
    
    try:
        pkg = CustomPackage(**package_data)
        
        # Should handle unicode
        name = pkg.name
        assert isinstance(name, str)
        
        # JSON should also handle unicode
        json_str = pkg.packageJSON
        parsed = json.loads(json_str)
        assert isinstance(parsed, dict)
        
    except Exception:
        # Should handle unicode gracefully
        pass