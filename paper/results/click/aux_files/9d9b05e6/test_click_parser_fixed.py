import math
from hypothesis import given, strategies as st, assume, settings, example
import click.parser as parser
from click.parser import _unpack_args, _split_opt, _normalize_opt


@given(
    st.lists(st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), min_size=1), min_size=0, max_size=20),
    st.integers(min_value=-1, max_value=10)
)
def test_unpack_args_single_nargs_bug(args, nargs):
    assume(nargs >= -1)
    
    unpacked, remaining = _unpack_args(args, [nargs])
    
    if nargs == 0:
        print(f"nargs=0: unpacked={unpacked}, type={type(unpacked)}, remaining={remaining}")
        assert isinstance(unpacked, tuple)
        if unpacked != ():
            print(f"Expected empty tuple, got {unpacked}")


@given(
    st.lists(st.text(min_size=0), min_size=0, max_size=10),
    st.lists(st.integers(min_value=1, max_value=3), min_size=1, max_size=3),
    st.lists(st.integers(min_value=1, max_value=3), min_size=1, max_size=3)
)
def test_unpack_args_wildcard_middle_bug(args, nargs_before, nargs_after):
    nargs_spec = nargs_before + [-1] + nargs_after
    
    unpacked, remaining = _unpack_args(args, nargs_spec)
    
    total_before = sum(nargs_before)
    total_after = sum(nargs_after)
    
    wildcard_idx = len(nargs_before)
    wildcard_content = unpacked[wildcard_idx]
    
    if isinstance(wildcard_content, tuple):
        wildcard_count = len(wildcard_content)
        total_consumed = total_before + wildcard_count + total_after
        
        if total_consumed > len(args):
            print(f"Bug found: total_consumed={total_consumed} > len(args)={len(args)}")
            print(f"args={args}, nargs_spec={nargs_spec}")
            print(f"unpacked={unpacked}, remaining={remaining}")
            print(f"nargs_before={nargs_before}, nargs_after={nargs_after}")
            print(f"wildcard_content={wildcard_content}")


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short", "-s"])