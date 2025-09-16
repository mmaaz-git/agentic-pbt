"""Analysis of potential bug in parse_yaml_list function."""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/copier_env/lib/python3.13/site-packages')

import yaml

# Reproduce the parse_yaml_list function logic
def parse_yaml_list_reproduction(string: str) -> list[str]:
    """Reproduction of parse_yaml_list to analyze potential issues."""
    node = yaml.compose(string, Loader=yaml.SafeLoader)
    
    if not isinstance(node, yaml.nodes.SequenceNode):
        raise ValueError(f"Not a YAML list: {string!r}")
    
    items = []
    for item in node.value:
        # Extract raw string from the original YAML
        raw = string[item.start_mark.index : item.end_mark.index].strip()
        
        # Special handling for quoted strings
        if (
            isinstance(item, yaml.nodes.ScalarNode)
            and item.tag == "tag:yaml.org,2002:str"
        ):
            # Strip quotes if the value is quoted
            if (raw.startswith('"') and raw.endswith('"')) or (
                raw.startswith("'") and raw.endswith("'")
            ):
                raw = raw[1:-1]
        
        items.append(raw)
    
    return items


# Test cases that might reveal bugs
test_cases = [
    # Case 1: List with nested structure
    """
- [1, 2, 3]
- simple
    """,
    
    # Case 2: List with multiline strings
    """
- |
  multiline
  string
- simple
    """,
    
    # Case 3: List with escaped quotes
    '''
- "string with \\"escaped quotes\\""
- 'another'
    ''',
    
    # Case 4: Empty strings
    """
- ""
- ''
-
    """,
    
    # Case 5: Mixed quotes
    '''
- "double"
- 'single'
- no quotes
    ''',
]

print("Analyzing parse_yaml_list for potential bugs...")
print("=" * 60)

for i, test_yaml in enumerate(test_cases, 1):
    print(f"\nTest case {i}:")
    print("Input YAML:")
    print(test_yaml)
    
    try:
        result = parse_yaml_list_reproduction(test_yaml.strip())
        print(f"Result: {result}")
        print(f"Number of items: {len(result)}")
        
        # Try to reparse each item
        for j, item in enumerate(result):
            try:
                reparsed = yaml.safe_load(item)
                print(f"  Item {j}: '{item}' -> {reparsed} (type: {type(reparsed).__name__})")
            except Exception as e:
                print(f"  Item {j}: '{item}' -> ERROR: {e}")
                
    except Exception as e:
        print(f"ERROR: {e}")
    
    print("-" * 40)