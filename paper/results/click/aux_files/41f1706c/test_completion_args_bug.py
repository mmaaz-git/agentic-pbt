import os
from hypothesis import given, strategies as st, assume, settings
import click.shell_completion as shell_completion


# Generate environment variable values that could come from shells
@given(
    comp_words=st.text(),
    comp_cword=st.integers(min_value=0, max_value=100)
)
@settings(max_examples=1000)
def test_bash_complete_get_completion_args_never_crashes(comp_words, comp_cword):
    """BashComplete.get_completion_args should handle any COMP_WORDS/COMP_CWORD combo"""
    os.environ["COMP_WORDS"] = comp_words
    os.environ["COMP_CWORD"] = str(comp_cword)
    
    bash_complete = shell_completion.BashComplete(None, {}, "test", "TEST")
    
    # This should never crash, even with malformed input
    args, incomplete = bash_complete.get_completion_args()
    
    # Verify the return types
    assert isinstance(args, list)
    assert isinstance(incomplete, str)
    assert all(isinstance(arg, str) for arg in args)


@given(
    comp_words=st.text(),
    comp_cword=st.integers(min_value=0, max_value=100)
)
@settings(max_examples=1000)
def test_zsh_complete_get_completion_args_never_crashes(comp_words, comp_cword):
    """ZshComplete.get_completion_args should handle any COMP_WORDS/COMP_CWORD combo"""
    os.environ["COMP_WORDS"] = comp_words
    os.environ["COMP_CWORD"] = str(comp_cword)
    
    zsh_complete = shell_completion.ZshComplete(None, {}, "test", "TEST")
    
    # This should never crash
    args, incomplete = zsh_complete.get_completion_args()
    
    assert isinstance(args, list)
    assert isinstance(incomplete, str)
    assert all(isinstance(arg, str) for arg in args)


@given(
    comp_words=st.text(),
    comp_cword=st.text()
)
@settings(max_examples=1000)
def test_fish_complete_get_completion_args_never_crashes(comp_words, comp_cword):
    """FishComplete.get_completion_args should handle any COMP_WORDS/COMP_CWORD combo"""
    os.environ["COMP_WORDS"] = comp_words
    os.environ["COMP_CWORD"] = comp_cword
    
    fish_complete = shell_completion.FishComplete(None, {}, "test", "TEST")
    
    # This should never crash
    args, incomplete = fish_complete.get_completion_args()
    
    assert isinstance(args, list) 
    assert isinstance(incomplete, str)
    assert all(isinstance(arg, str) for arg in args)


# Test specific edge cases that are likely to occur
@given(st.sampled_from(['\r', '\n', '\t', ' ', '\r\n', '  ', '\t\t']))
def test_bash_complete_whitespace_only(whitespace):
    """Test BashComplete with whitespace-only COMP_WORDS"""
    os.environ["COMP_WORDS"] = whitespace
    os.environ["COMP_CWORD"] = "0"
    
    bash_complete = shell_completion.BashComplete(None, {}, "test", "TEST")
    args, incomplete = bash_complete.get_completion_args()
    
    assert isinstance(args, list)
    assert isinstance(incomplete, str)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "--tb=short"])