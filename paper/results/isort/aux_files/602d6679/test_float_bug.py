import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages')

from hypothesis import given, strategies as st, settings
from isort import files
from isort.settings import Config


@given(st.lists(st.floats(allow_nan=False, allow_infinity=False), min_size=1, max_size=5))
@settings(max_examples=10)
def test_float_in_paths(float_paths):
    """Test that find handles float values without crashing."""
    config = Config()
    skipped = []
    broken = []
    
    try:
        result = list(files.find(float_paths, config, skipped, broken))
        # If it doesn't crash, that's acceptable
        assert isinstance(result, list)
    except TypeError as e:
        if "float" in str(e):
            # This is the bug - floats cause TypeError
            assert False, f"find() crashed on float input: {e}"
        raise


# Run the test
test_float_in_paths()