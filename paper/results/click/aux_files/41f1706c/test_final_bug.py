import os
from hypothesis import given, strategies as st, assume, settings
import click.shell_completion as shell_completion


# Test with printable text that excludes null bytes
printable_text = st.text(alphabet=st.characters(blacklist_categories=('Cc',)))

@given(
    comp_words=printable_text,
    comp_cword=st.integers(min_value=0, max_value=100)
)
@settings(max_examples=1000)
def test_bash_complete_handles_all_inputs(comp_words, comp_cword):
    """BashComplete should handle any valid shell input without crashing"""
    os.environ["COMP_WORDS"] = comp_words
    os.environ["COMP_CWORD"] = str(comp_cword)
    
    bash_complete = shell_completion.BashComplete(None, {}, "test", "TEST")
    
    # This should never crash, even with out-of-bounds indices
    args, incomplete = bash_complete.get_completion_args()
    
    assert isinstance(args, list)
    assert isinstance(incomplete, str)
    assert all(isinstance(arg, str) for arg in args)


# Test the specific edge case we found
def test_bash_complete_empty_comp_words_high_index():
    """Test the bug: empty COMP_WORDS with high COMP_CWORD causes IndexError"""
    # When COMP_WORDS contains only whitespace, it splits to empty list
    # But COMP_CWORD can still be > 0, causing index error
    
    os.environ["COMP_WORDS"] = "\r"  # Results in empty list after split
    os.environ["COMP_CWORD"] = "1"   # Tries to access index 1 of empty list
    
    bash_complete = shell_completion.BashComplete(None, {}, "test", "TEST")
    
    # Currently this should crash with IndexError
    try:
        args, incomplete = bash_complete.get_completion_args()
        print(f"No error! args={args}, incomplete={repr(incomplete)}")
    except IndexError as e:
        print(f"Got IndexError as expected: {e}")
        raise  # Re-raise to show the test found the bug


# Minimal reproduction
def test_minimal_reproduction():
    """Minimal test case showing the bug"""
    os.environ["COMP_WORDS"] = "\r\n\t "  # All whitespace
    os.environ["COMP_CWORD"] = "1"
    
    bash_complete = shell_completion.BashComplete(None, {}, "mycmd", "TEST")
    
    # This will crash with IndexError
    args, incomplete = bash_complete.get_completion_args()


if __name__ == "__main__":
    import pytest 
    pytest.main([__file__, "-v", "--tb=short", "-k", "test_minimal"])