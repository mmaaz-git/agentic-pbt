import sys
sys.path.insert(0, "/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages")

import isort.wrap_modes as wrap_modes

# Test case that Hypothesis found
interface = {
    "statement": "from module import ",
    "imports": ["0"],
    "white_space": "    ",
    "indent": "    ",
    "line_length": 80,
    "comments": [],
    "line_separator": "\n",
    "comment_prefix": " #",
    "include_trailing_comma": False,
    "remove_comments": False,
}

# Test all formatters
for formatter_name in wrap_modes._wrap_modes:
    if formatter_name == "VERTICAL_GRID_GROUPED_NO_COMMA":
        continue
    
    formatter = wrap_modes._wrap_modes[formatter_name]
    interface_copy = interface.copy()
    interface_copy["imports"] = interface["imports"].copy()
    
    result = formatter(**interface_copy)
    
    open_count = result.count('(')
    close_count = result.count(')')
    
    if open_count != close_count:
        print(f"BUG: {formatter_name} has unbalanced parentheses")
        print(f"  Open: {open_count}, Close: {close_count}")
        print(f"  Result: {repr(result)}")
        print()