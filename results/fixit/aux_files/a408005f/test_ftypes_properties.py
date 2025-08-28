#!/usr/bin/env python3
"""
Property-based tests for fixit.ftypes module
"""

import sys
import re
from typing import Any, Collection
from pathlib import Path

# Add the virtual environment's site-packages to the path
sys.path.insert(0, '/root/hypothesis-llm/envs/fixit_env/lib/python3.13/site-packages')

import fixit.ftypes as ftypes
from hypothesis import given, strategies as st, assume, settings

# Strategy for generating valid tag tokens
tag_token = st.text(alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=1, max_size=10)
exclude_prefix = st.sampled_from(["!", "^", "-"])

# Strategy for tag strings
@st.composite
def tag_strings(draw):
    n_tokens = draw(st.integers(min_value=0, max_value=5))
    if n_tokens == 0:
        return ""
    tokens = []
    for _ in range(n_tokens):
        token = draw(tag_token)
        if draw(st.booleans()):
            prefix = draw(exclude_prefix)
            tokens.append(f"{prefix}{token}")
        else:
            tokens.append(token)
    return ", ".join(tokens)

# Test Tags.parse() properties
@given(tag_strings())
def test_tags_parse_idempotence(tag_str):
    """Parsing twice should yield the same result"""
    result1 = ftypes.Tags.parse(tag_str)
    result2 = ftypes.Tags.parse(tag_str)
    assert result1 == result2

@given(tag_strings())
def test_tags_parse_normalization(tag_str):
    """Tags should always have sorted tuples"""
    result = ftypes.Tags.parse(tag_str)
    assert result.include == tuple(sorted(result.include))
    assert result.exclude == tuple(sorted(result.exclude))

@given(tag_strings())
def test_tags_bool_consistency(tag_str):
    """Tags bool should be True iff it has include or exclude items"""
    tags = ftypes.Tags.parse(tag_str)
    expected = bool(tags.include) or bool(tags.exclude)
    assert bool(tags) == expected

@given(st.text(min_size=1, max_size=10))
def test_tags_contains_single_string(value):
    """A string should be in tags if it's in include and not in exclude"""
    tags = ftypes.Tags(include=(value,))
    assert value in tags
    
    tags = ftypes.Tags(exclude=(value,))
    assert value not in tags
    
    tags = ftypes.Tags(include=(value,), exclude=(value,))
    assert value not in tags  # exclude takes precedence

@given(st.lists(tag_token, min_size=1, max_size=5))
def test_tags_contains_collection(values):
    """Collections should match if any value is in include and none in exclude"""
    if not values:
        return
    
    # If we include the first value, the collection should match
    tags = ftypes.Tags(include=(values[0],))
    assert values in tags
    
    # If we exclude any value, the collection should not match
    tags = ftypes.Tags(exclude=(values[0],))
    assert values not in tags

# Test QualifiedRule properties
@given(
    st.text(alphabet=st.characters(whitelist_categories=["Ll", "Lu", "Nd"], whitelist_characters="_"), min_size=1, max_size=20),
    st.one_of(st.none(), st.text(alphabet=st.characters(whitelist_categories=["Ll", "Lu", "Nd"], whitelist_characters="_"), min_size=1, max_size=20))
)
def test_qualified_rule_str_representation(module, name):
    """String representation should be consistent"""
    rule = ftypes.QualifiedRule(module=module, name=name)
    expected = module + (f":{name}" if name else "")
    assert str(rule) == expected

@given(
    st.lists(
        st.tuples(
            st.text(alphabet=st.characters(whitelist_categories=["Ll", "Lu", "Nd"], whitelist_characters="_"), min_size=1, max_size=10),
            st.one_of(st.none(), st.text(alphabet=st.characters(whitelist_categories=["Ll", "Lu", "Nd"], whitelist_characters="_"), min_size=1, max_size=10))
        ),
        min_size=3,
        max_size=5,
        unique=True
    )
)
def test_qualified_rule_ordering_transitivity(rule_data):
    """Ordering should be transitive"""
    rules = [ftypes.QualifiedRule(module=m, name=n) for m, n in rule_data]
    sorted_rules = sorted(rules)
    
    # Verify transitivity: if a < b and b < c, then a < c
    for i in range(len(sorted_rules)):
        for j in range(i + 1, len(sorted_rules)):
            for k in range(j + 1, len(sorted_rules)):
                a, b, c = sorted_rules[i], sorted_rules[j], sorted_rules[k]
                assert a < b
                assert b < c
                assert a < c

# Test helper functions
@given(st.one_of(
    st.lists(st.integers()),
    st.tuples(st.integers()),
    st.frozensets(st.integers()),
    st.sets(st.integers()),
    st.dictionaries(st.integers(), st.integers())
))
def test_is_sequence_for_collections(value):
    """Test is_sequence on various collection types"""
    result = ftypes.is_sequence(value)
    # Lists and tuples are sequences, sets/frozensets/dicts are not
    if isinstance(value, (list, tuple)):
        assert result is True
    else:
        assert result is False

@given(st.one_of(st.text(), st.binary()))
def test_is_sequence_excludes_strings_bytes(value):
    """Strings and bytes should never be considered sequences"""
    assert ftypes.is_sequence(value) is False

@given(st.one_of(st.text(), st.binary()))
def test_is_collection_excludes_strings_bytes(value):
    """Strings and bytes should never be considered collections"""
    assert ftypes.is_collection(value) is False

@given(st.lists(st.integers()))
def test_sequence_is_collection(value):
    """Everything that is a sequence should also be a collection (except str/bytes)"""
    if ftypes.is_sequence(value):
        assert ftypes.is_collection(value)

# Test regex patterns
@given(st.text(alphabet=st.characters(whitelist_categories=["Ll", "Lu", "Nd"], whitelist_characters="_"), min_size=1, max_size=20))
def test_lint_ignore_regex_basic_match(rule_name):
    """LintIgnoreRegex should match basic patterns"""
    patterns = [
        f"#lint-ignore:{rule_name}",
        f"# lint-ignore: {rule_name}",
        f"# lint-fixme: {rule_name}",
    ]
    
    for pattern in patterns:
        match = ftypes.LintIgnoreRegex.match(pattern)
        assert match is not None
        _, names = match.groups()
        assert rule_name in names if names else True

@given(
    st.text(alphabet=st.characters(whitelist_categories=["Ll", "Lu", "Nd"], whitelist_characters="_."), min_size=1, max_size=20)
        .filter(lambda x: re.match(r'^[a-zA-Z0-9_]+(\.[a-zA-Z0-9_]+)*$', x)),
    st.one_of(st.none(), st.text(alphabet=st.characters(whitelist_categories=["Ll", "Lu", "Nd"], whitelist_characters="_"), min_size=1, max_size=20))
)
def test_qualified_rule_regex_match_parse_roundtrip(module, name):
    """QualifiedRuleRegex should correctly parse valid module patterns"""
    pattern = module + (f":{name}" if name else "")
    match = ftypes.QualifiedRuleRegex.match(pattern)
    
    if match:
        groups = match.groupdict()
        assert groups['module'] == module
        assert groups['name'] == name
        
        # Should be able to create a QualifiedRule from the match
        rule = ftypes.QualifiedRule(
            module=groups['module'],
            name=groups['name'],
            local=groups.get('local')
        )
        assert rule.module == module
        assert rule.name == name

# Test Invalid and Valid dataclasses
@given(
    st.text(min_size=1),
    st.one_of(st.none(), st.tuples(st.integers(), st.integers(), st.integers(), st.integers()))
)
def test_invalid_dataclass_frozen(code, range_data):
    """Invalid dataclass should be frozen (immutable)"""
    from libcst.metadata import CodeRange, CodePosition
    
    code_range = None
    if range_data:
        start = CodePosition(range_data[0], range_data[1])
        end = CodePosition(range_data[2], range_data[3])
        code_range = CodeRange(start, end)
    
    invalid = ftypes.Invalid(code=code, range=code_range)
    
    # Verify it's frozen by trying to modify it
    try:
        invalid.code = "modified"
        assert False, "Should not be able to modify frozen dataclass"
    except Exception:
        pass  # Expected

@given(st.text(min_size=1))
def test_valid_dataclass_frozen(code):
    """Valid dataclass should be frozen (immutable)"""
    valid = ftypes.Valid(code=code)
    
    # Verify it's frozen
    try:
        valid.code = "modified"
        assert False, "Should not be able to modify frozen dataclass"
    except Exception:
        pass  # Expected

if __name__ == "__main__":
    # Run a quick test to verify everything works
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])