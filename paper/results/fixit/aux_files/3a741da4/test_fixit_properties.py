#!/usr/bin/env python3
"""Property-based tests for fixit module using Hypothesis."""

import sys
import string
from pathlib import Path
from hypothesis import given, strategies as st, assume, settings

# Add the fixit env to path
sys.path.insert(0, '/root/hypothesis-llm/envs/fixit_env/lib/python3.13/site-packages')

import fixit
from fixit.ftypes import Tags, QualifiedRule, is_sequence, is_collection


# Strategy for valid tag names (alphanumeric + underscore)
tag_name = st.text(alphabet=string.ascii_lowercase + string.digits + "_", min_size=1, max_size=20)


@given(tags=st.lists(tag_name, min_size=0, max_size=10))
@settings(max_examples=100)
def test_tags_parse_idempotent(tags):
    """Test that parsing tags twice gives the same result (idempotent property)."""
    # Create a comma-separated string
    tag_string = ",".join(tags)
    
    # Parse once
    parsed1 = Tags.parse(tag_string)
    
    # Convert back to string and parse again
    # Reconstruct the string from the parsed tags
    reconstructed = ",".join(parsed1.include) + ("," if parsed1.include and parsed1.exclude else "") + ",".join("!" + e for e in parsed1.exclude)
    if reconstructed == ",":
        reconstructed = ""
    
    parsed2 = Tags.parse(reconstructed if reconstructed else None)
    
    # Should have same include/exclude sets
    assert set(parsed1.include) == set(parsed2.include)
    assert set(parsed1.exclude) == set(parsed2.exclude)


@given(
    include_tags=st.lists(tag_name, min_size=0, max_size=5),
    exclude_tags=st.lists(tag_name, min_size=0, max_size=5)
)
@settings(max_examples=100)
def test_tags_parse_exclude_syntax(include_tags, exclude_tags):
    """Test that tags with exclusion prefixes are parsed correctly."""
    # Build a tag string with explicit includes and excludes
    tag_parts = list(include_tags) + ["!" + tag for tag in exclude_tags]
    if not tag_parts:
        return  # Skip empty case
    
    tag_string = ",".join(tag_parts)
    parsed = Tags.parse(tag_string)
    
    # All include tags should be in parsed.include
    for tag in include_tags:
        assert tag.lower() in parsed.include
    
    # All exclude tags should be in parsed.exclude
    for tag in exclude_tags:
        assert tag.lower() in parsed.exclude


@given(
    include_tags=st.lists(tag_name, min_size=0, max_size=3),
    exclude_tags=st.lists(tag_name, min_size=1, max_size=3),
    test_tag=tag_name
)
@settings(max_examples=100)
def test_tags_exclusion_precedence(include_tags, exclude_tags, test_tag):
    """Test that exclusion rules take precedence over inclusion rules."""
    # Make sure test_tag is in both include and exclude
    include_with_test = list(include_tags) + [test_tag]
    exclude_with_test = list(exclude_tags) + [test_tag]
    
    tag_string = ",".join(include_with_test) + "," + ",".join("!" + e for e in exclude_with_test)
    tags = Tags.parse(tag_string)
    
    # The test_tag should NOT be contained because exclusion takes precedence
    assert test_tag.lower() not in tags


@given(tag_string=st.text(alphabet=string.ascii_letters + string.digits + "_,!^-", max_size=100))
@settings(max_examples=100)
def test_tags_parse_case_insensitive(tag_string):
    """Test that tag parsing is case-insensitive."""
    parsed_lower = Tags.parse(tag_string.lower())
    parsed_upper = Tags.parse(tag_string.upper())
    
    # Both should produce the same lowercase results
    assert parsed_lower.include == parsed_upper.include
    assert parsed_lower.exclude == parsed_upper.exclude


@given(
    module=st.text(alphabet=string.ascii_letters + string.digits + "_.", min_size=1, max_size=50),
    name=st.one_of(st.none(), st.text(alphabet=string.ascii_letters + string.digits + "_", min_size=1, max_size=30))
)
@settings(max_examples=100)
def test_qualified_rule_string_representation(module, name):
    """Test QualifiedRule string representation follows the documented pattern."""
    assume("." in module or module[0].isalpha())  # Basic module name validation
    
    rule = QualifiedRule(module=module, name=name)
    str_repr = str(rule)
    
    # Should follow pattern: module[:name]
    if name:
        assert str_repr == f"{module}:{name}"
    else:
        assert str_repr == module
    
    # String representation should be consistent
    assert str(rule) == str(rule)  # Same object gives same string


@given(
    rules=st.lists(
        st.tuples(
            st.text(alphabet=string.ascii_letters + "_", min_size=1, max_size=20),
            st.one_of(st.none(), st.text(alphabet=string.ascii_letters + "_", min_size=1, max_size=20))
        ),
        min_size=2,
        max_size=10
    )
)
@settings(max_examples=100)
def test_qualified_rule_comparison_consistency(rules):
    """Test that QualifiedRule comparison is consistent with string representation."""
    rule_objects = [QualifiedRule(module=m, name=n) for m, n in rules]
    
    # Sort by the objects
    sorted_by_obj = sorted(rule_objects)
    
    # Sort by string representation
    sorted_by_str = sorted(rule_objects, key=str)
    
    # Should be the same order
    assert sorted_by_obj == sorted_by_str


@given(value=st.one_of(
    st.lists(st.integers()),
    st.tuples(st.integers()),
    st.text(),
    st.binary(),
    st.dictionaries(st.text(), st.integers()),
    st.sets(st.integers())
))
@settings(max_examples=100)
def test_is_sequence_correct_classification(value):
    """Test that is_sequence correctly identifies sequences vs other types."""
    result = is_sequence(value)
    
    if isinstance(value, (list, tuple)):
        assert result is True
    elif isinstance(value, (str, bytes)):
        assert result is False  # strings and bytes are explicitly excluded
    else:
        assert result is False


@given(value=st.one_of(
    st.lists(st.integers()),
    st.sets(st.integers()),
    st.text(),
    st.binary(),
    st.dictionaries(st.text(), st.integers()),
    st.integers()
))
@settings(max_examples=100)
def test_is_collection_correct_classification(value):
    """Test that is_collection correctly identifies collections vs other types."""
    result = is_collection(value)
    
    if isinstance(value, (list, set, dict)):
        assert result is True
    elif isinstance(value, (str, bytes)):
        assert result is False  # strings and bytes are explicitly excluded
    elif isinstance(value, int):
        assert result is False
    # Note: dict is Iterable (iterates over keys)


@given(
    include_tags=st.lists(tag_name, min_size=0, max_size=5, unique=True),
    test_tags=st.lists(tag_name, min_size=1, max_size=3)
)
@settings(max_examples=100)
def test_tags_contains_with_collections(include_tags, test_tags):
    """Test Tags.__contains__ with collection inputs."""
    tag_string = ",".join(include_tags) if include_tags else None
    tags = Tags.parse(tag_string)
    
    # If tags has no include list, it should match any tags
    if not tags.include:
        assert test_tags in tags
    # If any test_tag is in include list, collection should be contained
    elif any(t.lower() in tags.include for t in test_tags):
        assert test_tags in tags
    else:
        assert test_tags not in tags


@given(empty_input=st.sampled_from([None, "", "   ", ","]))
@settings(max_examples=50)
def test_tags_parse_empty_input(empty_input):
    """Test that Tags.parse handles empty/whitespace input correctly."""
    tags = Tags.parse(empty_input)
    
    # Should produce empty Tags object
    assert tags.include == ()
    assert tags.exclude == ()
    assert not tags  # __bool__ should return False


# Test formatter registration property
def test_formatter_registration():
    """Test that formatter subclasses auto-register in FORMAT_STYLES."""
    from fixit.format import FORMAT_STYLES, Formatter
    
    # Base Formatter should be registered under None
    assert FORMAT_STYLES[None] == Formatter
    
    # Known formatters should be registered
    assert "black" in FORMAT_STYLES
    assert "ufmt" in FORMAT_STYLES
    
    # Create a test formatter and verify registration
    class TestFormatter(Formatter):
        STYLE = "test_formatter_xyz"
        
    # Should auto-register
    assert "test_formatter_xyz" in FORMAT_STYLES
    assert FORMAT_STYLES["test_formatter_xyz"] == TestFormatter