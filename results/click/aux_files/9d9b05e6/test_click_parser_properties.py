import math
import sys
from hypothesis import given, strategies as st, assume, settings, example
import click.parser as parser
from click.parser import _unpack_args, _split_opt, _normalize_opt, _OptionParser, _Option, _Argument, _ParsingState
from click.core import Option, Argument, Context


@given(st.text(min_size=1))
def test_split_opt_reconstruction(opt):
    prefix, value = _split_opt(opt)
    reconstructed = prefix + value
    assert reconstructed == opt


@given(st.text(min_size=1))
def test_split_opt_prefix_length(opt):
    prefix, value = _split_opt(opt)
    assert len(prefix) <= 2
    assert len(prefix) + len(value) == len(opt)


@given(
    st.lists(st.text(min_size=0), min_size=0, max_size=10),
    st.lists(st.integers(min_value=-1, max_value=5), min_size=0, max_size=10)
)
def test_unpack_args_total_consumed(args, nargs_spec):
    assume(not any(n < -1 for n in nargs_spec))
    assume(sum(1 for n in nargs_spec if n < 0) <= 1)
    
    try:
        unpacked, remaining = _unpack_args(args, nargs_spec)
    except TypeError:
        return
    
    total_unpacked = 0
    for item in unpacked:
        if item is None:
            continue
        elif isinstance(item, tuple):
            total_unpacked += sum(1 for x in item if x is not None)
        else:
            total_unpacked += 1
    
    assert total_unpacked + len(remaining) == len(args)


@given(
    st.lists(st.text(min_size=1), min_size=0, max_size=10),
    st.lists(st.integers(min_value=1, max_value=3), min_size=0, max_size=5)
)
def test_unpack_args_nargs_positive_invariant(args, nargs_spec):
    unpacked, remaining = _unpack_args(args, nargs_spec)
    
    for i, nargs in enumerate(nargs_spec):
        if i < len(unpacked):
            item = unpacked[i]
            if nargs == 1:
                assert item is None or isinstance(item, str)
            elif nargs > 1:
                assert item is None or (isinstance(item, tuple) and len(item) == nargs)


@given(st.text(min_size=1), st.one_of(st.none(), st.builds(Context)))
def test_normalize_opt_idempotence(opt, ctx):
    normalized_once = _normalize_opt(opt, ctx)
    normalized_twice = _normalize_opt(normalized_once, ctx)
    assert normalized_once == normalized_twice


@given(st.text(min_size=1))
def test_split_opt_first_char_prefix_relation(opt):
    prefix, value = _split_opt(opt)
    first_char = opt[:1]
    
    if first_char.isalnum():
        assert prefix == ""
        assert value == opt
    else:
        assert prefix != "" or value == opt
        if prefix:
            assert prefix[0] == first_char


@given(st.lists(st.integers(min_value=1, max_value=3), min_size=1, max_size=5))
def test_unpack_args_empty_input(nargs_spec):
    unpacked, remaining = _unpack_args([], nargs_spec)
    
    assert all(item is None or (isinstance(item, tuple) and all(x is None for x in item)) for item in unpacked)
    assert remaining == []


@given(
    st.lists(st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), min_size=1), min_size=1, max_size=20),
    st.integers(min_value=-1, max_value=10)
)
def test_unpack_args_single_nargs(args, nargs):
    assume(nargs >= -1)
    
    unpacked, remaining = _unpack_args(args, [nargs])
    
    if nargs == -1:
        assert len(unpacked) == 1
        assert unpacked[0] == tuple(args)
        assert remaining == []
    elif nargs == 0:
        assert unpacked == []
        assert remaining == args
    elif nargs == 1:
        assert len(unpacked) == 1
        if args:
            assert unpacked[0] == args[0]
            assert remaining == args[1:]
        else:
            assert unpacked[0] is None
            assert remaining == []
    else:
        assert len(unpacked) == 1
        if len(args) >= nargs:
            assert unpacked[0] == tuple(args[:nargs])
            assert remaining == args[nargs:]
        else:
            expected_tuple = tuple(args) + (None,) * (nargs - len(args))
            assert unpacked[0] == expected_tuple
            assert remaining == []


@given(st.text(min_size=2, alphabet=st.characters(min_codepoint=33, max_codepoint=126)))
def test_split_opt_double_prefix(opt):
    assume(not opt[0].isalnum())
    
    prefix, value = _split_opt(opt)
    
    if len(opt) > 1 and opt[1] == opt[0]:
        assert prefix == opt[:2]
        assert value == opt[2:]
    else:
        assert prefix == opt[:1]
        assert value == opt[1:]


@given(st.lists(st.text(min_size=0), min_size=0, max_size=20))
def test_unpack_args_wildcard_consumes_all(args):
    unpacked, remaining = _unpack_args(args, [-1])
    
    assert len(unpacked) == 1
    assert unpacked[0] == tuple(args)
    assert remaining == []


@given(
    st.lists(st.text(min_size=0), min_size=1, max_size=10),
    st.lists(st.integers(min_value=1, max_value=3), min_size=1, max_size=3),
    st.lists(st.integers(min_value=1, max_value=3), min_size=1, max_size=3)
)
def test_unpack_args_wildcard_middle(args, nargs_before, nargs_after):
    nargs_spec = nargs_before + [-1] + nargs_after
    
    unpacked, remaining = _unpack_args(args, nargs_spec)
    
    total_before = sum(nargs_before)
    total_after = sum(nargs_after)
    
    wildcard_idx = len(nargs_before)
    assert wildcard_idx < len(unpacked)
    wildcard_content = unpacked[wildcard_idx]
    
    if isinstance(wildcard_content, tuple):
        wildcard_count = len(wildcard_content)
        total_consumed = total_before + wildcard_count + total_after
        
        assert total_consumed <= len(args)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])