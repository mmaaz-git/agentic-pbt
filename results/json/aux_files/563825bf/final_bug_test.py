"""Final bug confirmation using Hypothesis"""

from hypothesis import given, strategies as st, settings
import json
import subprocess
import sys
import tempfile
from pathlib import Path


# Test with minimal valid JSON values
simple_json = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(),
    st.lists(st.integers(), max_size=3),
    st.dictionaries(st.text(min_size=1, max_size=5), st.integers(), max_size=3)
)


@given(st.lists(simple_json, min_size=1, max_size=5))
@settings(max_examples=10)
def test_json_lines_file_bug(data_list):
    """Property test: json.tool --json-lines should handle file input correctly"""
    
    # Create JSON Lines file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
        for item in data_list:
            json.dump(item, f)
            f.write('\n')
        input_file = f.name
    
    try:
        # This should work but doesn't due to the bug
        result = subprocess.run(
            [sys.executable, '-m', 'json.tool', '--json-lines', '--no-indent', input_file],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        # The bug: this always fails with "I/O operation on closed file"
        assert result.returncode == 0, f"Bug confirmed: {result.stderr}"
        
    finally:
        Path(input_file).unlink()


if __name__ == "__main__":
    print("Running Hypothesis test to confirm bug...")
    try:
        test_json_lines_file_bug()
    except AssertionError as e:
        print(f"✓ Bug confirmed via Hypothesis: {e}")