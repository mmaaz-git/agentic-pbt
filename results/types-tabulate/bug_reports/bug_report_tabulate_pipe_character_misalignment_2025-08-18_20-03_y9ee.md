# Bug Report: tabulate Pipe Character Causes Column Misalignment

**Target**: `tabulate.tabulate`  
**Severity**: Medium
**Bug Type**: Logic
**Date**: 2025-08-18

## Summary

When data contains pipe characters ('|'), several table formats (pipe, grid, orgtbl) produce misaligned columns because the pipe characters in data are not escaped or properly handled.

## Property-Based Test

```python
@given(table_data_strategy(), st.sampled_from(["simple", "grid", "pipe"]))
def test_consistent_column_alignment(data, fmt):
    """Property: Column alignment should be consistent across rows."""
    assume(len(data) >= 2)
    assume(all(len(row) == len(data[0]) for row in data))
    
    result = tabulate_func(data, tablefmt=fmt)
    lines = result.split('\n')
    
    if fmt in ["grid", "pipe"]:
        data_lines = [l for l in lines if '|' in l and not all(c in '|+- =' for c in l)]
        
        if len(data_lines) >= 2:
            sep_positions = []
            for line in data_lines:
                positions = [i for i, c in enumerate(line) if c == '|']
                sep_positions.append(positions)
            
            if sep_positions:
                first_pos = sep_positions[0]
                for pos in sep_positions[1:]:
                    assert pos == first_pos, f"Inconsistent column alignment in {fmt} format"
```

**Failing input**: `data=[[None], ['0|']]` with `fmt='pipe'`

## Reproducing the Bug

```python
import tabulate

data = [['normal'], ['with|pipe']]
result = tabulate.tabulate(data, tablefmt='pipe')
print(result)

for i, line in enumerate(result.split('\n')):
    pipe_positions = [j for j, c in enumerate(line) if c == '|']
    print(f"Line {i} pipe positions: {pipe_positions}")
```

## Why This Is A Bug

This violates the fundamental property of table formatting:
1. Column separators should be at consistent positions across all rows for proper visual alignment
2. Data containing special characters used by the format should be escaped or handled appropriately
3. The pipe character is valid data that users might want to display (e.g., showing command pipelines, logical OR operations)
4. This affects multiple formats that use '|' as separator: pipe, grid, orgtbl

## Fix

```diff
# In the formatting logic for pipe-based formats:
- row_string = separator.join(cell_values)
+ escaped_values = [value.replace('|', '\\|') for value in cell_values]
+ row_string = separator.join(escaped_values)
```

The pipe character in data should be escaped (e.g., as `\|`) or replaced with a similar Unicode character (e.g., `│` U+2502) when using formats that use `|` as a delimiter.