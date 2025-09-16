#!/usr/bin/env python3
"""Property-based tests for fixit.cli module"""

import sys
from pathlib import Path

# Add fixit to path
sys.path.insert(0, "/root/hypothesis-llm/envs/fixit_env/lib/python3.13/site-packages")

from hypothesis import given, strategies as st, assume, settings
import re

from fixit.ftypes import Tags, QualifiedRule, QualifiedRuleRegex
from fixit.config import parse_rule, ConfigError
from fixit.cli import splash
import io
from unittest.mock import patch
import click.testing


# Test 1: Tags parsing properties
@given(st.text(min_size=1, max_size=100))
def test_tags_parse_include_exclude_disjoint(tag_string):
    """Include and exclude sets should be disjoint after parsing"""
    tags = Tags.parse(tag_string)
    # The sets should never overlap
    assert set(tags.include).isdisjoint(set(tags.exclude))


@given(st.lists(st.text(min_size=1, max_size=20, alphabet=st.characters(min_codepoint=97, max_codepoint=122)), min_size=1, max_size=10))
def test_tags_parse_prefixes(tag_list):
    """Tags with !, ^, or - prefixes should go to exclude, others to include"""
    # Create a tag string with some having prefixes
    tag_parts = []
    expected_include = set()
    expected_exclude = set()
    
    for i, tag in enumerate(tag_list):
        # Make tag lowercase and alphanumeric only
        clean_tag = ''.join(c for c in tag.lower() if c.isalnum())
        if not clean_tag:
            clean_tag = f"tag{i}"
        
        if i % 3 == 0:
            tag_parts.append(f"!{clean_tag}")
            expected_exclude.add(clean_tag)
        elif i % 3 == 1:
            tag_parts.append(f"-{clean_tag}")
            expected_exclude.add(clean_tag)
        else:
            tag_parts.append(clean_tag)
            expected_include.add(clean_tag)
    
    tag_string = ",".join(tag_parts)
    tags = Tags.parse(tag_string)
    
    assert set(tags.include) == expected_include
    assert set(tags.exclude) == expected_exclude


@given(st.text())
def test_tags_parse_empty_or_none(tag_string):
    """Empty or whitespace-only strings should produce empty Tags"""
    if tag_string.strip() == "":
        tags = Tags.parse(tag_string)
        assert tags.include == ()
        assert tags.exclude == ()
        assert not tags  # __bool__ should return False


# Test 2: QualifiedRule parsing properties
@given(st.text(min_size=1, max_size=100))
def test_parse_rule_invalid_format_raises(rule_string):
    """Invalid rule formats should raise ConfigError"""
    # Test that non-matching patterns raise errors
    if not QualifiedRuleRegex.match(rule_string):
        try:
            parse_rule(rule_string, Path.cwd())
            assert False, f"Should have raised ConfigError for {rule_string!r}"
        except ConfigError:
            pass  # Expected


@given(
    st.from_regex(r"[a-zA-Z0-9_]+(\.[a-zA-Z0-9_]+)*", fullmatch=True),
    st.one_of(st.none(), st.from_regex(r"[a-zA-Z0-9_]+", fullmatch=True))
)
def test_parse_rule_round_trip(module, name):
    """Parsing a rule and converting back to string should preserve format"""
    if name:
        rule_string = f"{module}:{name}"
    else:
        rule_string = module
    
    parsed = parse_rule(rule_string, Path.cwd())
    
    # Round-trip property
    assert str(parsed) == rule_string
    
    # Check individual components
    assert parsed.module == module
    assert parsed.name == name


@given(st.from_regex(r"\.[a-zA-Z0-9_]+(\.[a-zA-Z0-9_]+)*", fullmatch=True))
def test_parse_rule_local_prefix(local_module):
    """Rules starting with . should be marked as local"""
    parsed = parse_rule(local_module, Path("/test/root"))
    
    assert parsed.local == "."
    assert parsed.root == Path("/test/root")
    assert parsed.module == local_module


# Test 3: splash() function pluralization
@given(st.integers(min_value=0, max_value=1000))
def test_splash_pluralization(count):
    """The splash function should use 'file' for 1 and 'files' for other counts"""
    visited = set(Path(f"file{i}.py") for i in range(count))
    
    # Capture the output
    with patch('click.secho') as mock_secho:
        splash(visited, set())
    
    # Check the call was made
    if mock_secho.called:
        call_args = mock_secho.call_args[0][0]
        
        if count == 1:
            assert "1 file" in call_args
            assert "files" not in call_args.replace("1 files", "")  # Exclude the case where it incorrectly says "1 files"
        else:
            assert f"{count} files" in call_args


@given(
    st.integers(min_value=0, max_value=100),
    st.integers(min_value=0, max_value=100)
)
def test_splash_dirty_vs_clean_display(visited_count, dirty_count):
    """splash should display different messages for clean vs dirty files"""
    assume(dirty_count <= visited_count)
    
    visited = set(Path(f"file{i}.py") for i in range(visited_count))
    dirty = set(Path(f"file{i}.py") for i in range(dirty_count))
    
    with patch('click.secho') as mock_secho:
        splash(visited, dirty)
    
    call_args = mock_secho.call_args[0][0]
    
    if dirty:
        # Should show error count
        assert "with errors" in call_args or "🛠️" in call_args
        assert "clean" not in call_args
    else:
        # Should show clean message
        assert "clean" in call_args or "🧼" in call_args
        assert "errors" not in call_args


# Test 4: Tags containment logic
@given(
    st.lists(st.text(min_size=1, max_size=10, alphabet=st.characters(min_codepoint=97, max_codepoint=122)), min_size=0, max_size=5),
    st.lists(st.text(min_size=1, max_size=10, alphabet=st.characters(min_codepoint=97, max_codepoint=122)), min_size=0, max_size=5),
    st.text(min_size=1, max_size=10, alphabet=st.characters(min_codepoint=97, max_codepoint=122))
)
def test_tags_containment_logic(include_list, exclude_list, test_tag):
    """Tags __contains__ should follow documented logic"""
    # Ensure lists don't overlap
    exclude_list = [t for t in exclude_list if t not in include_list]
    
    tags = Tags(
        include=tuple(include_list),
        exclude=tuple(exclude_list)
    )
    
    # Test the containment logic
    if test_tag in exclude_list:
        assert test_tag not in tags
    elif not include_list or test_tag in include_list:
        assert test_tag in tags
    else:
        assert test_tag not in tags


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])