#!/usr/bin/env python3
"""
Property-based tests for the fixit module using Hypothesis.
"""

import sys
import re
from pathlib import Path
from hypothesis import given, strategies as st, assume, settings
import pytest

# Import fixit modules
from fixit.ftypes import Tags, QualifiedRule, QualifiedRuleRegex, Config
from fixit.util import capture, append_sys_path


# Strategy for tag tokens (excluding special characters at start)
tag_strategy = st.text(
    alphabet=st.characters(min_codepoint=97, max_codepoint=122) | st.characters(min_codepoint=48, max_codepoint=57),
    min_size=1,
    max_size=10
)

# Strategy for comma-separated tag strings
tags_string_strategy = st.lists(
    st.one_of(
        tag_strategy,  # normal tag
        tag_strategy.map(lambda s: f"!{s}"),  # excluded tag with !
        tag_strategy.map(lambda s: f"^{s}"),  # excluded tag with ^
        tag_strategy.map(lambda s: f"-{s}"),  # excluded tag with -
    ),
    min_size=0,
    max_size=5
).map(lambda tags: ", ".join(tags))


@given(tags_string_strategy)
def test_tags_parse_contains_consistency(tags_str):
    """Test that Tags.parse creates a Tags object with consistent containment logic."""
    tags = Tags.parse(tags_str)
    
    # Extract the actual tags from the string
    if tags_str:
        tokens = {t.strip() for t in tags_str.split(",")}
        for token in tokens:
            if token:
                # Get the actual tag name (without prefix)
                if token[0] in "!^-":
                    tag_name = token[1:].lower()
                    # Excluded tags should not be contained
                    assert tag_name not in tags
                else:
                    tag_name = token.lower()
                    # Included tags should be contained (unless also excluded)
                    if tag_name not in tags.exclude:
                        assert tag_name in tags


@given(tags_string_strategy)
def test_tags_parse_exclude_precedence(tags_str):
    """Test that exclude tags take precedence over include tags."""
    tags = Tags.parse(tags_str)
    
    # Verify that no excluded tag is ever contained
    for excluded in tags.exclude:
        assert excluded not in tags


@given(
    include=st.lists(tag_strategy, min_size=0, max_size=3, unique=True),
    exclude=st.lists(tag_strategy, min_size=0, max_size=3, unique=True)
)
def test_tags_direct_construction(include, exclude):
    """Test Tags constructed directly behaves correctly."""
    tags = Tags(include=tuple(include), exclude=tuple(exclude))
    
    # Test containment logic
    for inc in include:
        if inc not in exclude:
            assert inc in tags
    
    for exc in exclude:
        assert exc not in tags


# Strategy for valid Python module names
module_name_strategy = st.from_regex(r"[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)*", fullmatch=True)
# Strategy for valid Python identifier names  
identifier_strategy = st.from_regex(r"[a-zA-Z_][a-zA-Z0-9_]*", fullmatch=True)


@given(
    module=module_name_strategy,
    name=st.one_of(st.none(), identifier_strategy)
)
def test_qualified_rule_string_representation(module, name):
    """Test QualifiedRule string representation is consistent."""
    rule = QualifiedRule(module=module, name=name)
    
    # Test string representation
    if name:
        assert str(rule) == f"{module}:{name}"
    else:
        assert str(rule) == module
    
    # Test that the string can be parsed back (round-trip)
    match = QualifiedRuleRegex.match(str(rule))
    assert match is not None
    assert match.group("module") == module
    assert match.group("name") == name


@given(module_name_strategy)
def test_qualified_rule_regex_module_only(module):
    """Test QualifiedRuleRegex correctly parses module-only rules."""
    match = QualifiedRuleRegex.match(module)
    assert match is not None
    assert match.group("module") == module
    assert match.group("name") is None


@given(
    module=module_name_strategy,
    name=identifier_strategy
)
def test_qualified_rule_regex_with_name(module, name):
    """Test QualifiedRuleRegex correctly parses module:name rules."""
    rule_str = f"{module}:{name}"
    match = QualifiedRuleRegex.match(rule_str)
    assert match is not None
    assert match.group("module") == module
    assert match.group("name") == name


def test_qualified_rule_local_module():
    """Test QualifiedRuleRegex correctly identifies local modules."""
    # Test local module (starts with .)
    match = QualifiedRuleRegex.match(".local.module")
    assert match is not None
    assert match.group("module") == ".local.module"
    assert match.group("local") == "."
    
    # Test non-local module
    match = QualifiedRuleRegex.match("regular.module")
    assert match is not None
    assert match.group("module") == "regular.module"
    assert match.group("local") is None


# Test the capture utility
@given(st.lists(st.integers(), min_size=0, max_size=10))
def test_capture_basic_iteration(values):
    """Test that capture correctly iterates through generator values."""
    def gen():
        for v in values:
            yield v
        return len(values)
    
    captured = capture(gen())
    collected = list(captured)
    
    assert collected == values
    assert captured.result == len(values)


def test_capture_result_before_completion():
    """Test that accessing result before completion raises ValueError."""
    def gen():
        yield 1
        yield 2
        return 42
    
    captured = capture(gen())
    
    # Try to access result before iteration completes
    with pytest.raises(ValueError, match="Generator hasn't completed"):
        _ = captured.result


@given(st.lists(st.integers(), min_size=1, max_size=5))
def test_capture_send_respond(values):
    """Test capture's respond functionality."""
    def gen():
        results = []
        for v in values:
            response = yield v
            if response is not None:
                results.append(response)
        return results
    
    captured = capture(gen())
    collected = []
    for i, val in enumerate(captured):
        collected.append(val)
        if i % 2 == 0:  # Respond to even indices
            captured.respond(val * 2)
    
    assert collected == values
    # Check that responses were collected
    expected_responses = [values[i] * 2 for i in range(len(values)) if i % 2 == 0]
    assert captured.result == expected_responses


# Test append_sys_path context manager
@given(
    path_str=st.text(
        alphabet=st.characters(min_codepoint=65, max_codepoint=122),
        min_size=1,
        max_size=20
    ).filter(lambda s: "/" not in s and "\\" not in s)
)
def test_append_sys_path_restoration(path_str):
    """Test that append_sys_path restores sys.path after exit."""
    # Create a path that's unlikely to already exist in sys.path
    test_path = Path(f"/tmp/test_{path_str}")
    
    original_path = sys.path.copy()
    
    with append_sys_path(test_path):
        # Path should be in sys.path during context
        assert test_path.as_posix() in sys.path
    
    # Path should be removed after context (if it wasn't there originally)
    if test_path.as_posix() not in original_path:
        assert test_path.as_posix() not in sys.path
    
    # sys.path should be restored to original
    assert sys.path == original_path


def test_append_sys_path_no_duplicates():
    """Test that append_sys_path doesn't add duplicates."""
    test_path = Path("/tmp/test_no_dup")
    
    # First, ensure it's not in sys.path
    if test_path.as_posix() in sys.path:
        sys.path.remove(test_path.as_posix())
    
    original_len = len(sys.path)
    
    # Add it manually first
    sys.path.append(test_path.as_posix())
    
    with append_sys_path(test_path):
        # Should not add duplicate
        assert sys.path.count(test_path.as_posix()) == 1
    
    # Should still be there after context (since it was there before)
    assert test_path.as_posix() in sys.path
    
    # Clean up
    sys.path.remove(test_path.as_posix())


# Test Config path resolution idempotence
@given(
    path_str=st.text(
        alphabet=st.characters(min_codepoint=97, max_codepoint=122) | st.just("/"),
        min_size=1,
        max_size=20
    ).filter(lambda s: not s.startswith("//"))
)
def test_config_path_resolution_idempotent(path_str):
    """Test that Config path resolution is idempotent."""
    # Create a config with a relative path
    config1 = Config(path=Path(path_str))
    
    # Path should be resolved
    assert config1.path.is_absolute()
    
    # Create another config with the already-resolved path
    config2 = Config(path=config1.path)
    
    # Should be the same
    assert config1.path == config2.path


@given(st.integers(min_value=0, max_value=100))
def test_qualified_rule_comparison(seed):
    """Test QualifiedRule comparison operators."""
    # Generate some rule names deterministically from seed
    rules = []
    for i in range(3):
        module = f"module{(seed + i) % 10}"
        name = f"rule{(seed + i) % 5}" if i % 2 == 0 else None
        rules.append(QualifiedRule(module=module, name=name))
    
    # Test less-than operator
    for i in range(len(rules)):
        for j in range(len(rules)):
            if i != j:
                result = rules[i] < rules[j]
                expected = str(rules[i]) < str(rules[j])
                assert result == expected


if __name__ == "__main__":
    # Run with increased examples for thorough testing
    pytest.main([__file__, "-v", "--tb=short"])