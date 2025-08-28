import sys
sys.path.insert(0, "/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages")

import isort.wrap_modes as wrap_modes

interface = {
    "statement": "from module import ",
    "imports": ["foo"],
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
print(f"VERTICAL result for imports=['foo']: '{result}'")
print(f"Length: {len(result)}")
print(f"Is empty: {result == ''}")

# This is a bug: VERTICAL returns empty string for non-empty imports
assert result != "", "VERTICAL should not return empty string for non-empty imports"