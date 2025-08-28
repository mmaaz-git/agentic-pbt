#!/usr/bin/env python3
"""
Extended property-based tests for fixit.ftypes module
"""

import sys
import re
from typing import Any, Collection
from pathlib import Path

# Add the virtual environment's site-packages to the path
sys.path.insert(0, '/root/hypothesis-llm/envs/fixit_env/lib/python3.13/site-packages')

import fixit.ftypes as ftypes
from hypothesis import given, strategies as st, assume, settings, example

# Increase max_examples for more thorough testing
extended_settings = settings(max_examples=1000, deadline=None)

# Strategy for generating valid tag tokens  
tag_token = st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=1, max_size=10)

# More complex tag strings with edge cases
@st.composite
def complex_tag_strings(draw):
    """Generate complex tag strings including edge cases"""
    n_tokens = draw(st.integers(min_value=0, max_value=10))
    if n_tokens == 0:
        return draw(st.sampled_from(["", " ", "  ", "\t"]))
    
    tokens = []
    for _ in range(n_tokens):
        token = draw(tag_token)
        # More varied prefixes
        if draw(st.booleans()):
            prefix = draw(st.sampled_from(["!", "^", "-", "!!", "^^", "--"]))
            tokens.append(f"{prefix}{token}")
        else:
            tokens.append(token)
    
    # Various separators
    separator = draw(st.sampled_from([", ", ",", " ,", " , ", "  ,  "])    )
    return separator.join(tokens)

# Test for duplicate tokens in tags
@given(st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=1, max_size=5))
@extended_settings
def test_tags_parse_handles_duplicates(token):
    """Tags should handle duplicate tokens correctly"""
    # Same token multiple times
    tag_str = f"{token}, {token}, {token}"
    tags = ftypes.Tags.parse(tag_str)
    # Should only appear once in the tuple
    assert tags.include.count(token) == 1
    
    # Same token with different prefixes
    tag_str = f"{token}, !{token}"
    tags = ftypes.Tags.parse(tag_str)
    assert token in tags.include
    assert token in tags.exclude

# Test case sensitivity
@given(st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=10))
@extended_settings  
def test_tags_parse_case_handling(token):
    """Tags should handle case consistently"""
    upper = token.upper()
    lower = token.lower()
    mixed = "".join(c.upper() if i % 2 else c for i, c in enumerate(token))
    
    tag_str = f"{upper}, {lower}, {mixed}"
    tags = ftypes.Tags.parse(tag_str)
    
    # All should be lowercased
    for item in tags.include:
        assert item.islower()

# Test edge cases for QualifiedRule comparison
@given(
    st.text(alphabet=st.characters(whitelist_categories=["Ll", "Lu", "Nd"], whitelist_characters="_"), min_size=1, max_size=50),
    st.text(alphabet=st.characters(whitelist_categories=["Ll", "Lu", "Nd"], whitelist_characters="_"), min_size=1, max_size=50),
)
@extended_settings
def test_qualified_rule_comparison_consistency(module1, module2):
    """QualifiedRule comparison should be consistent"""
    rule1 = ftypes.QualifiedRule(module=module1)
    rule2 = ftypes.QualifiedRule(module=module2)
    
    # Comparison should be consistent
    if rule1 < rule2:
        assert not (rule2 < rule1)
        assert rule1 != rule2
    elif rule2 < rule1:
        assert not (rule1 < rule2)
        assert rule1 != rule2
    else:
        assert rule1 == rule2

# Test QualifiedRule with same module but different names
@given(
    st.text(alphabet=st.characters(whitelist_categories=["Ll", "Lu", "Nd"], whitelist_characters="_"), min_size=1, max_size=20),
    st.text(alphabet=st.characters(whitelist_categories=["Ll", "Lu", "Nd"], whitelist_characters="_"), min_size=1, max_size=20),
    st.text(alphabet=st.characters(whitelist_categories=["Ll", "Lu", "Nd"], whitelist_characters="_"), min_size=1, max_size=20),
)
@extended_settings
def test_qualified_rule_name_ordering(module, name1, name2):
    """Rules with same module should order by name"""
    assume(name1 != name2)
    
    rule1 = ftypes.QualifiedRule(module=module, name=name1)
    rule2 = ftypes.QualifiedRule(module=module, name=name2)
    
    str1 = str(rule1)
    str2 = str(rule2)
    
    if str1 < str2:
        assert rule1 < rule2
    elif str2 < str1:
        assert rule2 < rule1
    else:
        assert rule1 == rule2

# Test regex with special characters that should NOT match
@given(st.text())
@extended_settings
def test_qualified_rule_regex_invalid_patterns(text):
    """QualifiedRuleRegex should reject invalid patterns"""
    # Add some invalid characters
    if any(c in text for c in ['/', '-', ' ', '(', ')', '[', ']', '{', '}', '@', '#', '$', '%', '^', '&', '*']):
        match = ftypes.QualifiedRuleRegex.match(text)
        if match:
            # If it matches, it should only contain valid characters
            module = match.group('module')
            name = match.group('name')
            
            # Verify module only contains valid characters
            assert all(c.isalnum() or c in '._' for c in module)
            if name:
                assert all(c.isalnum() or c == '_' for c in name)

# Test Tags containment edge cases
@given(st.lists(st.text(min_size=0, max_size=5), min_size=0, max_size=10))
@extended_settings
def test_tags_contains_empty_collections(values):
    """Test Tags containment with empty and non-empty collections"""
    tags = ftypes.Tags()  # Empty tags
    
    # Empty tags should contain everything except when explicit include is set
    assert values in tags
    
    # With explicit include
    tags = ftypes.Tags(include=("something",))
    if not any(v == "something" for v in values):
        assert values not in tags

# Test is_sequence and is_collection with more types
@given(st.one_of(
    st.integers(),
    st.floats(),
    st.booleans(),
    st.none(),
    st.text(),
    st.binary(),
    st.lists(st.integers()),
    st.tuples(st.integers()),
    st.sets(st.integers()),
    st.frozensets(st.integers()),
    st.dictionaries(st.text(), st.integers()),
))
@extended_settings
def test_is_sequence_is_collection_comprehensive(value):
    """Comprehensive test for is_sequence and is_collection"""
    is_seq = ftypes.is_sequence(value)
    is_coll = ftypes.is_collection(value)
    
    # Basic types that are not sequences or collections
    if isinstance(value, (int, float, bool, type(None))):
        assert not is_seq
        assert not is_coll
    
    # Strings and bytes - special case
    elif isinstance(value, (str, bytes)):
        assert not is_seq
        assert not is_coll
    
    # Lists and tuples are both sequences and collections
    elif isinstance(value, (list, tuple)):
        assert is_seq
        assert is_coll
    
    # Sets, frozensets, dicts are collections but not sequences
    elif isinstance(value, (set, frozenset, dict)):
        assert not is_seq
        assert is_coll

# Test LintIgnoreRegex with complex patterns
@given(st.lists(st.text(alphabet=st.characters(whitelist_categories=["Ll", "Lu", "Nd"], whitelist_characters="_"), min_size=1, max_size=10), min_size=1, max_size=5))
@extended_settings
def test_lint_ignore_regex_multiple_rules(rule_names):
    """LintIgnoreRegex should handle multiple rule names"""
    rules_str = ", ".join(rule_names)
    patterns = [
        f"#lint-ignore:{rules_str}",
        f"# lint-ignore: {rules_str}",
        f"# lint-fixme: {rules_str}",
    ]
    
    for pattern in patterns:
        match = ftypes.LintIgnoreRegex.match(pattern)
        assert match is not None
        _, names = match.groups()
        # All rule names should be present
        for rule in rule_names:
            assert rule in names

# Test special case: empty string module (should this be allowed?)
@given(st.booleans())
def test_qualified_rule_empty_module_edge_case(use_empty):
    """Test QualifiedRule with edge case module names"""
    try:
        if use_empty:
            # Empty module - the regex shouldn't match empty string
            match = ftypes.QualifiedRuleRegex.match("")
            assert match is None
        else:
            # Single character module
            match = ftypes.QualifiedRuleRegex.match("x")
            assert match is not None
            assert match.group('module') == 'x'
    except Exception as e:
        # If it raises an exception, that's a bug
        assert False, f"Unexpected exception: {e}"

# Test Config dataclass post_init
@given(st.text(min_size=1, max_size=100))
def test_config_path_resolution(path_str):
    """Config should resolve paths in post_init"""
    try:
        # Create a config with a relative path
        config = ftypes.Config(path=Path(path_str))
        # Path should be resolved to absolute
        assert config.path.is_absolute()
    except (ValueError, OSError):
        # Some path strings might be invalid on the OS
        pass

# Property: Tags.parse should be deterministic
@given(complex_tag_strings())
@example("")
@example(" ")
@example("foo")
@example("!foo")
@example("foo, bar, !baz")
@extended_settings
def test_tags_parse_deterministic(tag_str):
    """Tags.parse should always produce the same result for the same input"""
    results = [ftypes.Tags.parse(tag_str) for _ in range(10)]
    # All results should be identical
    for r in results[1:]:
        assert r == results[0]

if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short", "-x"])