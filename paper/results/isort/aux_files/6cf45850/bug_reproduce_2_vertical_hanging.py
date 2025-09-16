import sys
sys.path.insert(0, "/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages")

import isort.wrap_modes as wrap_modes

interface = {
    "statement": "from module import ",
    "imports": [],  # Empty imports
    "white_space": "    ",
    "indent": "    ",
    "line_length": 80,
    "comments": [],
    "line_separator": "\n",
    "comment_prefix": " #",
    "include_trailing_comma": False,
    "remove_comments": False,
}

result = wrap_modes.vertical_hanging_indent(**interface)
print(f"VERTICAL_HANGING_INDENT result for empty imports: '{result}'")
print(f"Repr: {repr(result)}")
print(f"Is empty: {result == ''}")

# Check if it returns empty string as expected
if result != "":
    print("BUG: VERTICAL_HANGING_INDENT should return empty string for empty imports")
    print(f"Instead got: {repr(result)}")