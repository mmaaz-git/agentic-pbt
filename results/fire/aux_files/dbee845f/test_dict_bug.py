#!/usr/bin/env python3
"""Focused test to investigate the dictionary key bug."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/fire_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings
import fire.completion as completion


@given(st.dictionaries(
    st.text(min_size=1).filter(lambda x: not x.startswith('_') and '_' in x),
    st.none(),
    min_size=1
))
def test_dict_keys_with_underscores(d):
    """Dictionary keys with underscores are being transformed unexpectedly."""
    completions = completion.Completions(d)
    
    for key in d.keys():
        if '_' in key:
            assert key not in completions
            assert key.replace('_', '-') in completions
        else:
            assert key in completions


if __name__ == "__main__":
    test_dict_keys_with_underscores()
    print("Test passed!")