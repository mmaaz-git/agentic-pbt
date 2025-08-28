#!/usr/bin/env python3
"""Property-based tests for troposphere.oam module."""

import sys
import os
import json
sys.path.insert(0, '/root/hypothesis-llm/envs/troposphere_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings
import pytest

import troposphere.oam as oam


# Strategies for generating valid values
# Troposphere only accepts ASCII alphanumeric titles (matching regex ^[a-zA-Z0-9]+$)
valid_title_strategy = st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', min_size=1, max_size=50)
string_strategy = st.text(min_size=0, max_size=100)
filter_string_strategy = st.text(min_size=1, max_size=500)  # Filter strings should be non-empty


# Test 1: Round-trip property for LinkFilter
@given(filter_str=filter_string_strategy)
def test_linkfilter_round_trip(filter_str):
    """Test that LinkFilter survives to_dict/from_dict round-trip."""
    original = oam.LinkFilter(Filter=filter_str)
    
    # Convert to dict and back
    dict_repr = original.to_dict()
    reconstructed = oam.LinkFilter._from_dict(**dict_repr)
    
    # They should be equal
    assert original.to_dict() == reconstructed.to_dict()
    assert original.Filter == reconstructed.Filter


# Test 2: Round-trip property for LinkConfiguration
@given(
    log_filter=st.one_of(st.none(), filter_string_strategy),
    metric_filter=st.one_of(st.none(), filter_string_strategy)
)
def test_linkconfiguration_round_trip(log_filter, metric_filter):
    """Test that LinkConfiguration survives to_dict/from_dict round-trip."""
    kwargs = {}
    if log_filter is not None:
        kwargs['LogGroupConfiguration'] = oam.LinkFilter(Filter=log_filter)
    if metric_filter is not None:
        kwargs['MetricConfiguration'] = oam.LinkFilter(Filter=metric_filter)
    
    if not kwargs:
        # Empty LinkConfiguration
        original = oam.LinkConfiguration()
    else:
        original = oam.LinkConfiguration(**kwargs)
    
    # Convert to dict and back
    dict_repr = original.to_dict()
    reconstructed = oam.LinkConfiguration._from_dict(**dict_repr)
    
    # They should be equal
    assert original.to_dict() == reconstructed.to_dict()


# Test 3: Round-trip property for Link
@given(
    title=valid_title_strategy,
    label_template=st.one_of(st.none(), string_strategy),
    resource_types=st.lists(string_strategy, min_size=1, max_size=10),
    sink_identifier=string_strategy.filter(lambda x: len(x) > 0),
    tags=st.one_of(st.none(), st.dictionaries(string_strategy, string_strategy, max_size=10))
)
def test_link_round_trip(title, label_template, resource_types, sink_identifier, tags):
    """Test that Link survives to_dict/from_dict round-trip."""
    kwargs = {
        'ResourceTypes': resource_types,
        'SinkIdentifier': sink_identifier
    }
    
    if label_template is not None:
        kwargs['LabelTemplate'] = label_template
    if tags is not None:
        kwargs['Tags'] = tags
    
    original = oam.Link(title, **kwargs)
    
    # Convert to dict and back
    dict_repr = original.to_dict()
    # Extract properties for reconstruction
    props = dict_repr.get('Properties', {})
    reconstructed = oam.Link.from_dict(title, props)
    
    # They should have the same dict representation
    assert original.to_dict() == reconstructed.to_dict()


# Test 4: Round-trip property for Sink
@given(
    title=valid_title_strategy,
    name=string_strategy.filter(lambda x: len(x) > 0),
    policy=st.one_of(st.none(), st.dictionaries(string_strategy, string_strategy, max_size=5)),
    tags=st.one_of(st.none(), st.dictionaries(string_strategy, string_strategy, max_size=10))
)
def test_sink_round_trip(title, name, policy, tags):
    """Test that Sink survives to_dict/from_dict round-trip."""
    kwargs = {'Name': name}
    
    if policy is not None:
        kwargs['Policy'] = policy
    if tags is not None:
        kwargs['Tags'] = tags
    
    original = oam.Sink(title, **kwargs)
    
    # Convert to dict and back
    dict_repr = original.to_dict()
    # Extract properties for reconstruction
    props = dict_repr.get('Properties', {})
    reconstructed = oam.Sink.from_dict(title, props)
    
    # They should have the same dict representation
    assert original.to_dict() == reconstructed.to_dict()


# Test 5: Required field validation for Link
@given(
    title=valid_title_strategy,
    label_template=st.one_of(st.none(), string_strategy),
    tags=st.one_of(st.none(), st.dictionaries(string_strategy, string_strategy, max_size=10))
)
def test_link_required_fields_validation(title, label_template, tags):
    """Test that Link raises error when required fields are missing."""
    # Create Link without required fields
    kwargs = {}
    if label_template is not None:
        kwargs['LabelTemplate'] = label_template
    if tags is not None:
        kwargs['Tags'] = tags
    
    # This should work - object can be created
    link = oam.Link(title, **kwargs)
    
    # But validation should fail when converting to_dict
    with pytest.raises(ValueError, match="Resource.*required"):
        link.to_dict()


# Test 6: Required field validation for Sink
@given(
    title=valid_title_strategy,
    policy=st.one_of(st.none(), st.dictionaries(string_strategy, string_strategy, max_size=5)),
    tags=st.one_of(st.none(), st.dictionaries(string_strategy, string_strategy, max_size=10))
)
def test_sink_required_fields_validation(title, policy, tags):
    """Test that Sink raises error when required fields are missing."""
    # Create Sink without required Name field
    kwargs = {}
    if policy is not None:
        kwargs['Policy'] = policy
    if tags is not None:
        kwargs['Tags'] = tags
    
    # This should work - object can be created
    sink = oam.Sink(title, **kwargs)
    
    # But validation should fail when converting to_dict
    with pytest.raises(ValueError, match="Resource.*required"):
        sink.to_dict()


# Test 7: Title validation
@given(title=st.text(min_size=1, max_size=50))
def test_title_validation(title):
    """Test that only ASCII alphanumeric titles are accepted."""
    # Troposphere uses regex ^[a-zA-Z0-9]+$ for validation
    import re
    valid_names = re.compile(r"^[a-zA-Z0-9]+$")
    is_valid = bool(valid_names.match(title))
    
    if is_valid:
        # Should succeed
        link = oam.Link(title, ResourceTypes=['AWS::Logs::LogGroup'], SinkIdentifier='test')
        assert link.title == title
    else:
        # Should raise ValueError for non-alphanumeric titles
        with pytest.raises(ValueError, match="not alphanumeric"):
            oam.Link(title, ResourceTypes=['AWS::Logs::LogGroup'], SinkIdentifier='test')


# Test 8: Equality property
@given(
    title=valid_title_strategy,
    resource_types=st.lists(string_strategy, min_size=1, max_size=10),
    sink_identifier=string_strategy.filter(lambda x: len(x) > 0)
)
def test_link_equality(title, resource_types, sink_identifier):
    """Test that two Links with same properties are equal."""
    link1 = oam.Link(title, ResourceTypes=resource_types, SinkIdentifier=sink_identifier)
    link2 = oam.Link(title, ResourceTypes=resource_types, SinkIdentifier=sink_identifier)
    
    assert link1 == link2
    assert hash(link1) == hash(link2)


# Test 9: Type validation for Link ResourceTypes
@given(
    title=valid_title_strategy,
    resource_types=st.one_of(
        st.text(),  # Wrong type - should be list
        st.integers(),  # Wrong type
        st.lists(st.integers(), min_size=1)  # Wrong element type - need at least one element to trigger type check
    )
)
def test_link_resource_types_type_validation(title, resource_types):
    """Test that Link ResourceTypes only accepts list of strings."""
    with pytest.raises(TypeError):
        oam.Link(title, ResourceTypes=resource_types, SinkIdentifier='test')


# Test 10: LinkFilter required field validation
def test_linkfilter_required_field():
    """Test that LinkFilter requires Filter field."""
    lf = oam.LinkFilter()
    with pytest.raises(ValueError, match="Resource.*required"):
        lf.to_dict()


# Test 11: Complex nested structure round-trip
@given(
    title=valid_title_strategy,
    log_filter=st.one_of(st.none(), filter_string_strategy),
    metric_filter=st.one_of(st.none(), filter_string_strategy),
    label_template=st.one_of(st.none(), string_strategy),
    resource_types=st.lists(string_strategy, min_size=1, max_size=10),
    sink_identifier=string_strategy.filter(lambda x: len(x) > 0),
    tags=st.one_of(st.none(), st.dictionaries(string_strategy, string_strategy, max_size=10))
)
def test_link_with_configuration_round_trip(title, log_filter, metric_filter, label_template, resource_types, sink_identifier, tags):
    """Test Link with nested LinkConfiguration survives round-trip."""
    kwargs = {
        'ResourceTypes': resource_types,
        'SinkIdentifier': sink_identifier
    }
    
    # Add LinkConfiguration if we have filters
    if log_filter is not None or metric_filter is not None:
        config_kwargs = {}
        if log_filter is not None:
            config_kwargs['LogGroupConfiguration'] = oam.LinkFilter(Filter=log_filter)
        if metric_filter is not None:
            config_kwargs['MetricConfiguration'] = oam.LinkFilter(Filter=metric_filter)
        kwargs['LinkConfiguration'] = oam.LinkConfiguration(**config_kwargs)
    
    if label_template is not None:
        kwargs['LabelTemplate'] = label_template
    if tags is not None:
        kwargs['Tags'] = tags
    
    original = oam.Link(title, **kwargs)
    
    # Convert to dict and back
    dict_repr = original.to_dict()
    props = dict_repr.get('Properties', {})
    reconstructed = oam.Link.from_dict(title, props)
    
    # They should have the same dict representation
    assert original.to_dict() == reconstructed.to_dict()


if __name__ == "__main__":
    # Run a quick smoke test
    test_linkfilter_round_trip()
    test_link_equality()
    print("Quick smoke test passed!")