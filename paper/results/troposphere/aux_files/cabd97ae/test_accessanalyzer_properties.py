#!/usr/bin/env python3
"""Property-based tests for troposphere.accessanalyzer module."""

import math
import sys
import os

# Add virtual environment to path
sys.path.insert(0, "/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages")

from hypothesis import assume, given, strategies as st, settings
import troposphere.accessanalyzer as aa
from troposphere.validators import boolean, integer


# Strategy for valid alphanumeric titles (required by troposphere)
valid_titles = st.text(alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")), min_size=1, max_size=100)

# Strategy for strings that may contain special characters
arbitrary_strings = st.text(min_size=0, max_size=100)

# Strategy for Filter objects with required properties
@st.composite
def filter_strategy(draw):
    """Generate valid Filter objects with required Property field."""
    filter_obj = aa.Filter(
        Property=draw(arbitrary_strings),  # Required field
        Contains=draw(st.one_of(st.none(), st.lists(arbitrary_strings, max_size=10))),
        Eq=draw(st.one_of(st.none(), st.lists(arbitrary_strings, max_size=10))),
        Exists=draw(st.one_of(st.none(), st.booleans())),
        Neq=draw(st.one_of(st.none(), st.lists(arbitrary_strings, max_size=10)))
    )
    return filter_obj


# Test 1: Round-trip property for Filter objects
@given(filter_obj=filter_strategy())
@settings(max_examples=100)
def test_filter_round_trip(filter_obj):
    """Test that Filter objects can be serialized and deserialized correctly."""
    # Convert to dict
    filter_dict = filter_obj.to_dict()
    
    # Create new Filter from dict
    reconstructed = aa.Filter.from_dict(None, filter_dict)
    
    # The reconstructed object should be equal to the original
    assert reconstructed.to_dict() == filter_dict


# Test 2: ArchiveRule round-trip with required fields
@st.composite
def archive_rule_strategy(draw):
    """Generate valid ArchiveRule objects with all required fields."""
    rule = aa.ArchiveRule(
        RuleName=draw(arbitrary_strings),  # Required
        Filter=draw(st.lists(filter_strategy(), min_size=1, max_size=5))  # Required, non-empty list
    )
    return rule


@given(archive_rule=archive_rule_strategy())
@settings(max_examples=100)
def test_archive_rule_round_trip(archive_rule):
    """Test ArchiveRule serialization/deserialization."""
    rule_dict = archive_rule.to_dict()
    reconstructed = aa.ArchiveRule.from_dict(None, rule_dict)
    assert reconstructed.to_dict() == rule_dict


# Test 3: Boolean validator property
@given(
    value=st.one_of(
        st.just(True), st.just(False),
        st.just(1), st.just(0),
        st.just("true"), st.just("false"),
        st.just("True"), st.just("False"),
        st.just("1"), st.just("0")
    )
)
def test_boolean_validator_valid_inputs(value):
    """Test that boolean validator accepts valid boolean representations."""
    result = boolean(value)
    assert isinstance(result, bool)
    
    # Verify correct conversion
    if value in [True, 1, "1", "true", "True"]:
        assert result is True
    else:
        assert result is False


@given(
    value=st.one_of(
        st.integers(min_value=2),  # Numbers other than 0, 1
        st.text(min_size=1).filter(lambda x: x not in ["true", "false", "True", "False", "1", "0"]),
        st.floats(),
        st.lists(st.integers())
    )
)
def test_boolean_validator_invalid_inputs(value):
    """Test that boolean validator rejects invalid inputs."""
    try:
        boolean(value)
        assert False, f"Expected ValueError for input {value}"
    except ValueError:
        pass  # Expected


# Test 4: Integer validator property  
@given(value=st.integers())
def test_integer_validator_accepts_integers(value):
    """Test that integer validator accepts actual integers."""
    result = integer(value)
    assert int(result) == value


@given(value=st.text(alphabet="0123456789-", min_size=1))
def test_integer_validator_accepts_numeric_strings(value):
    """Test that integer validator accepts numeric strings."""
    # Filter out invalid patterns
    assume(value != "-" and not value.startswith("--"))
    assume(value.count("-") <= 1)
    if "-" in value:
        assume(value.startswith("-"))
    
    try:
        int(value)  # This should work if it's a valid integer string
        result = integer(value)
        assert int(result) == int(value)
    except ValueError:
        # If int() fails, integer() should also fail
        try:
            integer(value)
            assert False, f"integer() should have failed for {value}"
        except ValueError:
            pass


@given(
    value=st.one_of(
        st.text(min_size=1).filter(lambda x: not x.lstrip("-").isdigit()),
        st.floats().filter(lambda x: not x.is_integer()),
        st.lists(st.integers())
    )
)
def test_integer_validator_rejects_non_integers(value):
    """Test that integer validator rejects non-integer values."""
    try:
        integer(value)
        assert False, f"Expected ValueError for non-integer input {value}"
    except ValueError:
        pass  # Expected


# Test 5: Analyzer with required Type field
@st.composite
def analyzer_strategy(draw):
    """Generate Analyzer objects with required Type field."""
    analyzer = aa.Analyzer(
        title=draw(valid_titles),
        Type=draw(st.sampled_from(["ACCOUNT", "ORGANIZATION", "ACCOUNT_UNUSED_ACCESS", "ORGANIZATION_UNUSED_ACCESS"])),  # Required field
        AnalyzerName=draw(st.one_of(st.none(), arbitrary_strings))
    )
    return analyzer


@given(analyzer=analyzer_strategy())
@settings(max_examples=100)
def test_analyzer_has_required_type(analyzer):
    """Test that Analyzer objects maintain their required Type field."""
    analyzer_dict = analyzer.to_dict()
    assert "Type" in analyzer_dict["Properties"]
    
    # Round-trip test
    reconstructed = aa.Analyzer.from_dict(analyzer.title, analyzer_dict["Properties"])
    assert reconstructed.Type == analyzer.Type


# Test 6: Title validation property
@given(title=valid_titles)
def test_valid_titles_accepted(title):
    """Test that valid alphanumeric titles are accepted."""
    obj = aa.Analyzer(title=title, Type="ACCOUNT")
    assert obj.title == title


@given(
    title=st.text(min_size=1).filter(
        lambda x: not x.replace("_", "").replace("-", "").replace(" ", "").isalnum()
    )
)
def test_invalid_titles_rejected(title):
    """Test that titles with special characters are rejected."""
    # Filter to ensure we have actual special characters
    assume(any(c in title for c in "!@#$%^&*()+={}[]|\\:;\"'<>,.?/~` -_"))
    
    try:
        aa.Analyzer(title=title, Type="ACCOUNT")
        assert False, f"Expected ValueError for title with special characters: {title}"
    except ValueError as e:
        assert "not alphanumeric" in str(e)


if __name__ == "__main__":
    # Run all tests
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])