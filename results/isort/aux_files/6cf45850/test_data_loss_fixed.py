import sys
sys.path.insert(0, "/root/hypothesis-llm/envs/isort_env/lib/python3.13/site-packages")

import re
import copy
import isort.wrap_modes as wrap_modes

def test_data_loss(imports_list):
    """Test that all import names appear in the formatted output."""
    base_interface = {
        "statement": "from module import ",
        "white_space": "    ",
        "indent": "    ",
        "line_length": 80,
        "comments": [],
        "line_separator": "\n",
        "comment_prefix": " #",
        "include_trailing_comma": False,
        "remove_comments": False,
    }
    
    for formatter_name in wrap_modes._wrap_modes:
        if formatter_name == "VERTICAL_GRID_GROUPED_NO_COMMA":
            continue
        
        # Create a deep copy of the interface for each formatter
        interface = copy.deepcopy(base_interface)
        interface["imports"] = imports_list.copy()
        
        formatter = wrap_modes._wrap_modes[formatter_name]
        result = formatter(**interface)
        
        for import_name in imports_list:
            escaped_name = re.escape(import_name)
            if not re.search(escaped_name, result):
                return formatter_name, import_name, result
    
    return None

# Test with the inputs that Hypothesis found
test_cases = [
    ["0"],
    ["a", "b"],
    ["foo", "bar", "baz"],
    ["!", "@", "#"],
]

for imports in test_cases:
    issue = test_data_loss(imports)
    if issue:
        formatter_name, lost_import, result = issue
        print(f"BUG: {formatter_name} lost import '{lost_import}'")
        print(f"  Imports: {imports}")
        print(f"  Result: {repr(result)}")
        print()