#!/usr/bin/env python3
"""
Property-based tests for fixit regex patterns.
"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fixit_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, example
import pytest

from fixit.ftypes import (
    LintIgnoreRegex, 
    QualifiedRuleRegex,
    QualifiedRule,
    is_sequence,
    is_collection
)


# Test LintIgnoreRegex pattern
@given(
    prefix_spaces=st.text(alphabet=" ", min_size=0, max_size=3),
    directive=st.sampled_from(["lint-ignore", "lint-fixme"]),
    separator=st.sampled_from([":", " ", "  "]),
    rules=st.lists(
        st.from_regex(r"[a-zA-Z_][a-zA-Z0-9_]*", fullmatch=True),
        min_size=0,
        max_size=3
    )
)
def test_lint_ignore_regex_valid_patterns(prefix_spaces, directive, separator, rules):
    """Test that LintIgnoreRegex matches valid lint directive patterns."""
    # Construct a valid lint directive
    if rules:
        rules_str = ", ".join(rules)
        line = f"#{prefix_spaces}{directive}{separator}{rules_str}"
    else:
        line = f"#{prefix_spaces}{directive}"
    
    match = LintIgnoreRegex.search(line)
    assert match is not None
    
    # Verify captured groups
    assert match.group(1) == directive
    if rules:
        # Should capture the rules
        captured_rules = match.group(2)
        assert captured_rules is not None
        # Parse captured rules
        parsed_rules = [r.strip() for r in captured_rules.split(",")]
        assert parsed_rules == rules
    else:
        # No rules captured
        assert match.group(2) is None


def test_lint_ignore_regex_edge_cases():
    """Test edge cases for LintIgnoreRegex."""
    # Test without rules
    assert LintIgnoreRegex.search("# lint-ignore") is not None
    assert LintIgnoreRegex.search("#lint-fixme") is not None
    
    # Test with rules
    assert LintIgnoreRegex.search("# lint-ignore: rule1") is not None
    assert LintIgnoreRegex.search("# lint-ignore rule1, rule2") is not None
    
    # Test invalid patterns
    assert LintIgnoreRegex.search("lint-ignore") is None  # Missing #
    assert LintIgnoreRegex.search("# lintignore") is None  # Missing dash
    
    # Test with extra content
    match = LintIgnoreRegex.search("# lint-ignore: rule1  # extra comment")
    assert match is not None
    assert match.group(2) == "rule1"


# Test QualifiedRuleRegex pattern  
@given(
    local=st.booleans(),
    parts=st.lists(
        st.from_regex(r"[a-zA-Z_][a-zA-Z0-9_]*", fullmatch=True),
        min_size=1,
        max_size=3
    ),
    name=st.one_of(
        st.none(),
        st.from_regex(r"[a-zA-Z_][a-zA-Z0-9_]*", fullmatch=True)
    )
)
def test_qualified_rule_regex_valid(local, parts, name):
    """Test QualifiedRuleRegex with valid patterns."""
    # Construct module string
    module = ("." if local else "") + ".".join(parts)
    
    # Construct full rule string
    if name:
        rule_str = f"{module}:{name}"
    else:
        rule_str = module
    
    match = QualifiedRuleRegex.match(rule_str)
    assert match is not None
    
    # Verify captured groups
    assert match.group("module") == module
    assert match.group("name") == name
    assert match.group("local") == ("." if local else None)


def test_qualified_rule_regex_invalid():
    """Test QualifiedRuleRegex rejects invalid patterns."""
    invalid_patterns = [
        "",  # empty
        ".",  # just dot
        "..",  # double dot
        "module.",  # trailing dot
        ":name",  # missing module
        "module::",  # double colon
        "module:name:extra",  # extra colon
        "123module",  # starts with number
        "module-name",  # hyphen not allowed
        "module name",  # space not allowed
    ]
    
    for pattern in invalid_patterns:
        assert QualifiedRuleRegex.match(pattern) is None


# Test QualifiedRule parsing round-trip
@given(
    module=st.from_regex(r"\.?[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)*", fullmatch=True),
    name=st.one_of(
        st.none(),
        st.from_regex(r"[a-zA-Z_][a-zA-Z0-9_]*", fullmatch=True)
    )
)
def test_qualified_rule_parse_roundtrip(module, name):
    """Test that QualifiedRule string representation can be parsed back."""
    rule = QualifiedRule(module=module, name=name)
    rule_str = str(rule)
    
    # Parse the string representation
    match = QualifiedRuleRegex.match(rule_str)
    assert match is not None
    
    # Create new rule from parsed components
    parsed_rule = QualifiedRule(
        module=match.group("module"),
        name=match.group("name"),
        local=match.group("local")
    )
    
    # String representations should match
    assert str(parsed_rule) == rule_str


# Test is_sequence and is_collection helpers
@given(
    value=st.one_of(
        st.lists(st.integers()),
        st.tuples(st.integers()),
        st.sets(st.integers()),
        st.text(),
        st.binary(),
        st.integers(),
        st.dictionaries(st.text(), st.integers())
    )
)
def test_is_sequence_is_collection(value):
    """Test is_sequence and is_collection helper functions."""
    # is_sequence should return True for lists/tuples but not strings/bytes
    if isinstance(value, (list, tuple)) and not isinstance(value, (str, bytes)):
        assert is_sequence(value) == True
    else:
        assert is_sequence(value) == False
    
    # is_collection should return True for iterables except strings/bytes
    if hasattr(value, '__iter__') and not isinstance(value, (str, bytes)):
        assert is_collection(value) == True
    else:
        assert is_collection(value) == False


# Test specific regex edge cases found during exploration
def test_lint_ignore_regex_complex():
    """Test complex lint ignore patterns."""
    # Multiple rules with varied spacing
    match = LintIgnoreRegex.search("#  lint-ignore:  rule1  ,rule2,  rule3  ")
    assert match is not None
    assert match.group(1) == "lint-ignore"
    assert "rule1" in match.group(2)
    assert "rule2" in match.group(2)
    assert "rule3" in match.group(2)
    
    # With tabs
    match = LintIgnoreRegex.search("#\tlint-fixme:\trule1")
    assert match is not None
    
    # Case sensitivity (directive is case-sensitive)
    assert LintIgnoreRegex.search("# LINT-IGNORE") is None
    assert LintIgnoreRegex.search("# Lint-Ignore") is None


def test_qualified_rule_underscore_heavy():
    """Test QualifiedRule with lots of underscores."""
    # Underscores are valid in Python identifiers
    rule_str = "__private__.__module__:__rule__"
    match = QualifiedRuleRegex.match(rule_str)
    assert match is not None
    assert match.group("module") == "__private__.__module__"
    assert match.group("name") == "__rule__"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])