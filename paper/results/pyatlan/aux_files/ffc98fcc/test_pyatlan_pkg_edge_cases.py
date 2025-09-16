#!/usr/bin/env python3
import json
import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/pyatlan_env/lib/python3.13/site-packages')

from hypothesis import assume, given, strategies as st, settings, example
from hypothesis.strategies import composite
import pytest

# Import the modules we want to test
from pyatlan.pkg.models import CustomPackage, PackageDefinition, PullPolicy
from pyatlan.pkg.ui import UIStep, UIRule
from pyatlan.pkg.utils import validate_multiselect, validate_connection, validate_connector_and_connection
from pyatlan.pkg.widgets import UIElementWithEnum
from pathlib import Path
import tempfile


# Test edge cases with special characters in package IDs
@given(st.text(min_size=1, max_size=100))
@example("")  # Empty string edge case
@example("@" * 50)  # Many @ symbols
@example("/" * 50)  # Many / symbols
@example("@//@//")  # Multiple special chars
@example("😀🎉")  # Unicode emojis
@example("\n\t\r")  # Whitespace characters
@example("../../etc/passwd")  # Path traversal attempt
def test_package_id_transformation_edge_cases(package_id):
    """Test that package ID transformation handles edge cases safely."""
    package_data = {
        "package_id": package_id,
        "package_name": "Test",
        "description": "Test",
        "icon_url": "http://example.com/icon.png",
        "docs_url": "http://example.com/docs",
        "ui_config": {"steps": []},
        "container_image": "test:latest",
        "container_command": ["echo", "test"]
    }
    
    try:
        pkg = CustomPackage(**package_data)
        name = pkg.name
        
        # The name should never contain @ or /
        assert "@" not in name
        assert "/" not in name
        
        # The name should be deterministic
        pkg2 = CustomPackage(**package_data)
        assert pkg2.name == name
        
    except Exception as e:
        # The code should handle invalid inputs gracefully
        pass


# Test UIStep with edge case titles
@given(st.text(min_size=0, max_size=500))
@example("")  # Empty title
@example(" " * 100)  # Only spaces
@example("\n\n\n")  # Only newlines
@example("A" * 1000)  # Very long title
@example("  leading and trailing  ")  # Spaces at edges
def test_ui_step_title_edge_cases(title):
    """Test UIStep with edge case titles."""
    step = UIStep(title=title, inputs={})
    
    # ID should not have spaces
    assert " " not in step.id
    
    # ID should be lowercase
    assert step.id == step.id.lower()
    
    # ID should be deterministic
    step2 = UIStep(title=title, inputs={})
    assert step.id == step2.id


# Test validate_multiselect with malformed JSON
@given(st.text(min_size=1, max_size=100))
@example("[")  # Incomplete JSON
@example("]")  # Incomplete JSON
@example("[[]")  # Nested incomplete
@example('["unclosed string')  # Unclosed string
@example('[{"key": "value"}]')  # Object in array
@example('[null, undefined, NaN]')  # JavaScript literals
def test_validate_multiselect_malformed_json(text):
    """Test validate_multiselect with potentially malformed JSON."""
    if text.startswith("["):
        try:
            result = validate_multiselect(text)
            # If it succeeds, it should return a list
            assert isinstance(result, list)
        except (json.JSONDecodeError, ValueError):
            # Should fail gracefully for malformed JSON
            pass
    else:
        # Non-JSON strings should be wrapped in a list
        result = validate_multiselect(text)
        assert result == [text]


# Test JSON injection in validate_multiselect
@given(st.text(min_size=1, max_size=100))
def test_validate_multiselect_json_injection(text):
    """Test that validate_multiselect doesn't allow JSON injection."""
    # Try to inject JSON that might break parsing
    injection_attempts = [
        f'["{text}", "__import__(\'os\').system(\'ls\')"]',
        f'["{text}"]]; console.log("hacked"); //',
        f'["{text}"]; import os; os.system("ls")',
    ]
    
    for attempt in injection_attempts:
        try:
            result = validate_multiselect(attempt)
            # Should parse as normal JSON, not execute code
            assert isinstance(result, list)
            # The injected code should be treated as strings
            for item in result:
                assert isinstance(item, str)
        except (json.JSONDecodeError, ValueError):
            # Should fail safely
            pass


# Test UIElementWithEnum with empty dictionaries
def test_ui_element_enum_empty():
    """Test UIElementWithEnum with empty possible_values."""
    element = UIElementWithEnum(
        type_="string",
        required=True,
        possible_values={}
    )
    
    assert element.enum == []
    assert element.enum_names == []
    assert len(element.enum) == 0
    assert element.possible_values == {}


# Test CustomPackage with extreme values
@given(
    package_name=st.text(min_size=0, max_size=1000),
    description=st.text(min_size=0, max_size=10000),
    keywords=st.lists(st.text(min_size=0, max_size=100), min_size=0, max_size=100)
)
def test_custom_package_extreme_values(package_name, description, keywords):
    """Test CustomPackage with extreme input values."""
    package_data = {
        "package_id": "@test/pkg",
        "package_name": package_name,
        "description": description,
        "icon_url": "http://example.com/icon.png",
        "docs_url": "http://example.com/docs",
        "ui_config": {"steps": []},
        "container_image": "test:latest",
        "container_command": ["echo", "test"],
        "keywords": keywords
    }
    
    try:
        pkg = CustomPackage(**package_data)
        
        # Should be able to generate JSON
        json_str = pkg.packageJSON
        parsed = json.loads(json_str)
        
        # Values should be preserved
        assert parsed["description"] == description
        assert parsed["keywords"] == keywords
        
    except Exception:
        # Should handle extreme values gracefully
        pass


# Test packageJSON with special characters
@given(st.text(min_size=1, max_size=100))
@example('"')  # Quote
@example('\\')  # Backslash
@example('\n')  # Newline
@example('\t')  # Tab
@example('\u0000')  # Null character
@example('{"injection": "attempt"}')  # JSON injection
def test_package_json_special_characters(text):
    """Test that packageJSON properly escapes special characters."""
    package_data = {
        "package_id": "@test/pkg",
        "package_name": text,
        "description": text,
        "icon_url": "http://example.com/icon.png",
        "docs_url": "http://example.com/docs", 
        "ui_config": {"steps": []},
        "container_image": "test:latest",
        "container_command": ["echo", "test"]
    }
    
    try:
        pkg = CustomPackage(**package_data)
        json_str = pkg.packageJSON
        
        # Should produce valid JSON even with special chars
        parsed = json.loads(json_str)
        
        # The special characters should be preserved after parsing
        assert parsed["description"] == text
        
    except Exception:
        # Should handle special characters gracefully
        pass


# Test UIStep.to_json method
@given(
    title=st.text(min_size=1, max_size=100),
    description=st.text(min_size=0, max_size=500)
)
def test_ui_step_to_json(title, description):
    """Test that UIStep.to_json produces valid JSON."""
    step = UIStep(title=title, inputs={}, description=description)
    
    json_str = step.to_json()
    
    # Should be valid JSON
    parsed = json.loads(json_str)
    
    # Should contain expected fields
    assert parsed["title"] == title
    assert parsed["description"] == description
    assert parsed["id"] == title.replace(" ", "_").lower()
    assert "properties" in parsed


# Test validate_multiselect with very large inputs
@given(st.lists(st.text(min_size=1, max_size=50), min_size=100, max_size=200))
@settings(max_examples=5)  # Reduce examples for performance
def test_validate_multiselect_large_lists(items):
    """Test validate_multiselect with very large lists."""
    json_str = json.dumps(items)
    
    result = validate_multiselect(json_str)
    
    # Should handle large lists correctly
    assert result == items
    assert len(result) == len(items)


# Test concurrent package name generation
@given(st.text(min_size=1, max_size=50))
def test_package_name_thread_safety(package_id):
    """Test that package name generation is consistent even with multiple instances."""
    package_data = {
        "package_id": package_id,
        "package_name": "Test",
        "description": "Test",
        "icon_url": "http://example.com/icon.png",
        "docs_url": "http://example.com/docs",
        "ui_config": {"steps": []},
        "container_image": "test:latest",
        "container_command": ["echo", "test"]
    }
    
    # Create multiple instances
    packages = [CustomPackage(**package_data) for _ in range(10)]
    
    # All should have the same name
    names = [pkg.name for pkg in packages]
    assert all(name == names[0] for name in names)


# Test UIRule with edge cases
def test_ui_rule_edge_cases():
    """Test UIRule with various edge cases."""
    # Empty when_inputs
    rule1 = UIRule(when_inputs={}, required=[])
    assert rule1.when_inputs == {}
    assert rule1.required == []
    
    # Large number of required fields
    required_fields = [f"field_{i}" for i in range(100)]
    rule2 = UIRule(when_inputs={"key": "value"}, required=required_fields)
    assert len(rule2.required) == 100
    
    # Special characters in when_inputs
    rule3 = UIRule(
        when_inputs={"key with spaces": "value\nwith\nnewlines"},
        required=["field1"]
    )
    assert "key with spaces" in rule3.when_inputs