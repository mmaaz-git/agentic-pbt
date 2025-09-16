import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/awkward_env/lib/python3.13/site-packages')
from awkward.forth import ForthMachine64
from hypothesis import given, strategies as st


@given(st.integers(min_value=0, max_value=9),
       st.sampled_from(['dup', 'drop', 'swap', 'over', 'rot']))
def test_numeric_prefix_parsing_bug(digit, operation):
    """Test that numeric-prefixed operations are parsed incorrectly"""
    
    # Create a word that looks like a number followed by an operation
    word = f'{digit}{operation}'
    
    # The parser incorrectly treats this as just the number
    machine = ForthMachine64(word)
    machine.begin()
    machine.run()
    
    # The bug: it should error or implement the composite operation,
    # but instead just pushes the number
    assert machine.stack == [digit], f"'{word}' was parsed as literal {digit} instead of failing or implementing {digit}{operation}"


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])