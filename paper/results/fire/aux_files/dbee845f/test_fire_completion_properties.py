#!/usr/bin/env python3
"""Property-based tests for fire.completion module using Hypothesis."""

import sys
import os
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, assume, settings, HealthCheck
import fire.completion as completion
import math


@given(st.text())
def test_format_for_command_underscore_invariant(token):
    """Tokens starting with '_' should remain unchanged."""
    if token.startswith('_'):
        result = completion._FormatForCommand(token)
        assert result == token


@given(st.text(min_size=1).filter(lambda x: not x.startswith('_')))
def test_format_for_command_hyphen_replacement(token):
    """Tokens not starting with '_' should have underscores replaced with hyphens."""
    result = completion._FormatForCommand(token)
    assert '_' not in result
    assert result == token.replace('_', '-')


@given(st.one_of(
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.booleans(),
    st.none(),
    st.lists(st.integers()),
    st.tuples(st.text()),
))
def test_format_for_command_always_returns_string(token):
    """_FormatForCommand should always return a string."""
    result = completion._FormatForCommand(token)
    assert isinstance(result, str)


@given(st.dictionaries(st.text(), st.none()), st.text())
def test_member_visible_dunder_members_never_visible(component, name):
    """Members starting with '__' should never be visible."""
    if name.startswith('__'):
        assert completion.MemberVisible(component, name, None) is False
        assert completion.MemberVisible(component, name, None, verbose=True) is False
        assert completion.MemberVisible(component, name, None, verbose=False) is False


@given(st.dictionaries(st.text(min_size=1).filter(lambda x: x.startswith('_') and not x.startswith('__')), st.none()))
def test_member_visible_underscore_members_verbose(component):
    """Members starting with single '_' should be visible only when verbose=True."""
    for name in component.keys():
        assert completion.MemberVisible(component, name, component[name], verbose=True) is True
        assert completion.MemberVisible(component, name, component[name], verbose=False) is False


@given(st.lists(st.integers()))
def test_completions_list_indices(lst):
    """Completions for lists should be string indices from 0 to len-1."""
    completions = completion.Completions(lst)
    expected = [str(i) for i in range(len(lst))]
    assert set(completions) == set(expected)


@given(st.tuples(st.integers(), st.text(), st.floats(allow_nan=False)))
def test_completions_tuple_indices(tpl):
    """Completions for tuples should be string indices from 0 to len-1."""
    completions = completion.Completions(tpl)
    expected = [str(i) for i in range(len(tpl))]
    assert set(completions) == set(expected)


def generator_factory():
    """Creates a generator for testing."""
    def gen():
        x = 0
        while True:
            yield x
            x += 1
    return gen()


def test_completions_generator_empty():
    """Completions for generators should always be empty list."""
    gen = generator_factory()
    completions = completion.Completions(gen)
    assert completions == []


@given(st.dictionaries(
    st.text(min_size=1).filter(lambda x: not x.startswith('_')),
    st.one_of(st.integers(), st.text(), st.none())
))
def test_completions_dict_keys_not_values(d):
    """Completions for dicts should be the keys, not the values."""
    if not d:
        return
    completions = completion.Completions(d)
    for key in d.keys():
        assert key in completions
    for value in d.values():
        if value not in d.keys():
            assert value not in completions


@given(st.lists(st.from_regex(r'^[a-zA-Z_][a-zA-Z0-9_]*$', fullmatch=True), max_size=10))
@settings(suppress_health_check=[HealthCheck.filter_too_much])
def test_completions_from_args_prefix(args):
    """All completions from _CompletionsFromArgs should start with '--'."""
    completions = completion._CompletionsFromArgs(args)
    for comp in completions:
        assert comp.startswith('--')


@given(st.lists(st.from_regex(r'^[a-zA-Z][a-zA-Z0-9]*_[a-zA-Z0-9_]*$', fullmatch=True), max_size=10))
@settings(suppress_health_check=[HealthCheck.filter_too_much])
def test_completions_from_args_underscore_to_hyphen(args):
    """_CompletionsFromArgs should replace underscores with hyphens."""
    completions = completion._CompletionsFromArgs(args)
    for i, arg in enumerate(args):
        expected = f"--{arg.replace('_', '-')}"
        assert expected in completions


@given(st.text())
def test_is_option_property(arg):
    """_IsOption returns True if and only if arg starts with '-'."""
    result = completion._IsOption(arg)
    assert result == arg.startswith('-')


@given(st.dictionaries(
    st.text(min_size=1).filter(lambda x: not x.startswith('__')),
    st.none()
), st.booleans())
def test_visible_members_consistency(component, verbose):
    """VisibleMembers should only return members that MemberVisible returns True for."""
    members = completion.VisibleMembers(component, verbose=verbose)
    for name, member in members:
        assert completion.MemberVisible(component, name, member, verbose=verbose) is True


@given(st.lists(st.one_of(
    st.text(min_size=2).map(lambda x: f"-{x}"),
    st.text(min_size=1).filter(lambda x: not x.startswith('-'))
)))
def test_get_maps_option_classification(commands):
    """_GetMaps should correctly classify options (start with '-') vs subcommands."""
    name = "testcmd"
    commands_list = [[cmd] for cmd in commands]
    global_options, options_map, subcommands_map = completion._GetMaps(
        name, commands_list, set()
    )
    
    for opt in global_options:
        assert opt.startswith('-')
    
    for subcommand_set in subcommands_map.values():
        for subcommand in subcommand_set:
            if not subcommand.startswith('-'):
                continue


@given(st.lists(st.lists(st.text(min_size=1), min_size=1, max_size=3), min_size=1))
@settings(max_examples=100)
def test_get_maps_structure(commands):
    """Test that _GetMaps maintains consistent structure."""
    name = "testcmd"
    default_options = {"--help", "--version"}
    
    global_options, options_map, subcommands_map = completion._GetMaps(
        name, commands, default_options
    )
    
    assert isinstance(global_options, set)
    assert isinstance(options_map, dict)
    assert isinstance(subcommands_map, dict)
    
    assert default_options.issubset(global_options)
    
    for key in options_map:
        assert isinstance(options_map[key], set)
        assert default_options.issubset(options_map[key])
    
    for key in subcommands_map:
        assert isinstance(subcommands_map[key], set)