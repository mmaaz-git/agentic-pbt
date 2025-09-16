import sys
sys.path.insert(0, "/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages")

import isort.wrap_modes as wrap_modes

# Use the exact input that Hypothesis found
interface = {
    "statement": "from module import ",
    "imports": ["0"],  # The Hypothesis-found input
    "white_space": "    ",
    "indent": "    ",
    "line_length": 80,
    "comments": [],
    "line_separator": "\n",
    "comment_prefix": " #",
    "include_trailing_comma": False,
    "remove_comments": False,
}

result = wrap_modes.vertical(**interface)
print(f"VERTICAL result for imports=['0']: '{result}'")
print(f"Length: {len(result)}")
print(f"Repr: {repr(result)}")

# Check what the test was actually checking
assert len(result) > 0, "VERTICAL should return non-empty string for non-empty imports"